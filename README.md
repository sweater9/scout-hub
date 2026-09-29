# Scout Hub

Standalone scout app with three sub-tools:

1. **GitHub** — most starred / forked repos (Search API; optional `GITHUB_TOKEN`)
2. **AI News** — Hacker News Algolia + RSS feeds
3. **Free models** — curated free-tier APIs + Hugging Face popular models

## Run locally

```bash
pip install -r requirements.txt
export GITHUB_TOKEN=ghp_...   # optional, higher rate limits
python app.py
```

Open http://localhost:5000/

## Deploy (Render)

- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app --bind 0.0.0.0:$PORT`
- Optional env: `GITHUB_TOKEN`
