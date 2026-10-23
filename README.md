# ReelSave — Instagram & YouTube Video Downloader

FastAPI + yt-dlp website supporting public Instagram posts and Reels, YouTube watch links, Shorts and youtu.be links.

## Run locally

```bash
docker build -t reelsave .
docker run --rm -p 8000:8000 reelsave
```

Open http://localhost:8000.

## Render deployment

The existing Render service auto-deploys from `main`. Dockerfile builds the app; `/health` returns `{"status":"ok"}`.

## Limitations

YouTube and Instagram may block cloud IPs, require sign-in or enforce other restrictions. Some videos will fail. Maximum file size is 150 MB. The downloader chooses a single progressive format, prioritizing MP4 up to 720p where available; resolution or audio availability depends on the provider. This app does not bypass private content restrictions, DRM or authentication. Downloads temporarily use local disk and per-process concurrency and rate limiting; timeout does not cancel a running thread. Consider worker isolation, stricter traffic limits and bandwidth controls before broad public promotion.

Only download content you own or have permission to save. Not affiliated with Instagram, Meta, YouTube or Google.
