# ReelSave — Instagram Video Downloader

A responsive downloader for public Instagram Reels and posts using FastAPI and yt-dlp.

## Run locally

```bash
docker build -t reelsave .
docker run --rm -p 8000:8000 reelsave
```

Open http://localhost:8000.

## Deploy on Render

1. Create a **New Web Service** from this GitHub repository.
2. Select **Docker** runtime and **Free** instance type.
3. Use `./Dockerfile` and health check path `/health`.
4. Deploy. Render supplies a public HTTPS URL.

Alternatively use the included `render.yaml` as a Render Blueprint.

## Operational limitations

Instagram can block data-center IPs or require authentication, so some downloads will fail. This app does not bypass private-account restrictions. Limit usage and monitor hosting bandwidth. Temporary downloads are deleted after response completion. Rate limiting and concurrency controls are per process. The 90-second timeout does not terminate a blocked worker thread. For higher traffic, use isolated jobs and edge rate limiting.

Only download videos you own or have permission to save. Not affiliated with Instagram or Meta.
