"""Scout Hub — GitHub repos, AI news, free AI models."""
from __future__ import annotations

import os

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from scout import (
    fetch_ai_news,
    github_status as scout_github_status,
    list_free_models,
    models_status as scout_models_status,
    news_status as scout_news_status,
    search_repos,
)

app = Flask(__name__)
CORS(app)


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/scout")
def scout_page():
    return render_template("scout.html")


@app.route("/api/health")
def health():
    return jsonify({"ok": True, "service": "scout-hub"})


@app.route("/api/scout/github")
def api_scout_github():
    try:
        repos = search_repos(
            q=request.args.get("q", ""),
            language=request.args.get("language", ""),
            min_stars=int(request.args.get("min_stars") or 0),
            sort=request.args.get("sort", "stars"),
            per_page=int(request.args.get("per_page") or 20),
        )
        return jsonify({"repos": repos, "count": len(repos)})
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/scout/news")
def api_scout_news():
    try:
        items = fetch_ai_news(
            q=request.args.get("q", "AI"),
            limit=int(request.args.get("limit") or 20),
        )
        return jsonify({"items": items, "count": len(items)})
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/scout/models")
def api_scout_models():
    try:
        data = list_free_models(limit=int(request.args.get("limit") or 30))
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/scout/status")
def api_scout_status():
    return jsonify(
        {
            "github": scout_github_status(),
            "news": scout_news_status(),
            "models": scout_models_status(),
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
