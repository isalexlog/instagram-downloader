import asyncio
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.background import BackgroundTask

app = FastAPI(title="ReelSave", docs_url=None, redoc_url=None)
limiter = Limiter(key_func=get_remote_address, default_limits=["30/hour"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.mount("/static", StaticFiles(directory="static"), name="static")
semaphore = asyncio.Semaphore(2)
MAX_BYTES = 150 * 1024 * 1024

class DownloadRequest(BaseModel):
    url: str

def validate_url(value: str) -> tuple[str, str]:
    if len(value) > 2048:
        raise HTTPException(400, "URL is too long")
    try:
        parsed = urlparse(value)
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port:
            raise ValueError()
    except ValueError:
        raise HTTPException(400, "Provide a valid HTTPS Instagram or YouTube URL")
    host = (parsed.hostname or "").lower()
    if host in {"instagram.com", "www.instagram.com"}:
        if not re.fullmatch(r"/(reel|reels|p|tv)/[A-Za-z0-9_-]+/?", parsed.path):
            raise HTTPException(400, "Only Instagram posts and Reels are supported")
        return "https://www.instagram.com" + parsed.path, "instagram"
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            from urllib.parse import parse_qs
            vid = parse_qs(parsed.query).get("v", [""])[0]
        else:
            match = re.fullmatch(r"/(?:shorts|live|embed)/([A-Za-z0-9_-]{11})/?", parsed.path)
            vid = match.group(1) if match else ""
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
            raise HTTPException(400, "Provide a valid YouTube video or Shorts URL")
        return "https://www.youtube.com/watch?v=" + vid, "youtube"
    if host in {"youtu.be", "www.youtu.be"}:
        match = re.fullmatch(r"/([A-Za-z0-9_-]{11})/?", parsed.path)
        if not match:
            raise HTTPException(400, "Provide a valid youtu.be video URL")
        return "https://www.youtube.com/watch?v=" + match.group(1), "youtube"
    raise HTTPException(400, "Only Instagram and YouTube links are supported")

def fetch(url: str, folder: str) -> Path:
    opts = {
        "format": "best[ext=mp4][height<=720]/best[height<=720]/best[ext=mp4]/best",
        "outtmpl": str(Path(folder) / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "max_filesize": MAX_BYTES,
        "socket_timeout": 15,
        "retries": 1,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    files = [p for p in Path(folder).iterdir() if p.is_file()]
    if len(files) != 1:
        raise ValueError("Could not retrieve a single video")
    file = files[0]
    if file.stat().st_size > MAX_BYTES:
        raise ValueError("Video exceeds 150 MB")
    return file

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/download")
@limiter.limit("5/minute")
async def download(request: Request, payload: DownloadRequest):
    url, platform = validate_url(payload.url)
    if semaphore.locked():
        raise HTTPException(503, "Server busy, try again later")
    await semaphore.acquire()
    tmp = tempfile.TemporaryDirectory()
    try:
        file = await asyncio.wait_for(asyncio.to_thread(fetch, url, tmp.name), timeout=90)
        suffix = file.suffix.lower()
        if suffix not in {".mp4", ".m4v", ".mov", ".webm"}:
            raise ValueError("Unsupported video format")
        return FileResponse(file, media_type="video/mp4" if suffix == ".mp4" else "application/octet-stream",
                            filename=platform + "-video" + suffix, background=BackgroundTask(tmp.cleanup))
    except asyncio.TimeoutError:
        tmp.cleanup()
        raise HTTPException(504, "Video provider did not respond in time")
    except Exception:
        tmp.cleanup()
        raise HTTPException(422, "Unable to download. Video may be unavailable, restricted, or too large.")
    finally:
        semaphore.release()
