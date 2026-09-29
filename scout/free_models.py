"""Free / open AI models and free-tier API scout."""
from __future__ import annotations

from typing import Any

import requests

HF_MODELS_URL = "https://huggingface.co/api/models"
DEFAULT_TIMEOUT = 20
UA = {"User-Agent": "scout-hub/1.0"}

# Curated free-tier / open tools. access: "open" | "signup" | "local"
CURATED_FREE: list[dict[str, Any]] = [
    {
        "id": "gemini-free",
        "name": "Google Gemini (free tier)",
        "provider": "Google",
        "description": "Gemini API free tier via Google AI Studio — text, multimodal, generous rate limits for prototyping.",
        "url": "https://ai.google.dev/",
        "access": "signup",
        "kind": "api",
        "notes": "Requires free API key from AI Studio.",
    },
    {
        "id": "groq-free",
        "name": "Groq Cloud (free tier)",
        "provider": "Groq",
        "description": "Very fast inference on open models (Llama, Mixtral, Gemma) with a free developer tier.",
        "url": "https://console.groq.com/",
        "access": "signup",
        "kind": "api",
        "notes": "Free API key; rate-limited.",
    },
    {
        "id": "hf-inference-free",
        "name": "Hugging Face Inference API (free)",
        "provider": "Hugging Face",
        "description": "Serverless inference for thousands of open models; free tier with rate limits.",
        "url": "https://huggingface.co/docs/api-inference/",
        "access": "signup",
        "kind": "api",
        "notes": "HF account / token recommended for higher limits.",
    },
    {
        "id": "openrouter-free",
        "name": "OpenRouter free models",
        "provider": "OpenRouter",
        "description": "Unified API with a set of models marked :free — no credit needed for those routes.",
        "url": "https://openrouter.ai/models?q=free",
        "access": "signup",
        "kind": "api",
        "notes": "Account required; free models rotate over time.",
    },
    {
        "id": "ollama-local",
        "name": "Ollama (local)",
        "provider": "Ollama",
        "description": "Run open LLMs locally with a simple CLI and OpenAI-compatible HTTP API. Fully free, offline-capable.",
        "url": "https://ollama.com/",
        "access": "local",
        "kind": "local",
        "notes": "No signup; needs local install and GPU/CPU resources.",
    },
    {
        "id": "together-free",
        "name": "Together AI (free credits)",
        "provider": "Together",
        "description": "Open-model inference platform; new accounts often get free trial credits.",
        "url": "https://www.together.ai/",
        "access": "signup",
        "kind": "api",
        "notes": "Signup for free credits; check current promo.",
    },
    {
        "id": "cohere-trial",
        "name": "Cohere Trial",
        "provider": "Cohere",
        "description": "Command / Embed APIs with a free trial tier for developers.",
        "url": "https://cohere.com/",
        "access": "signup",
        "kind": "api",
        "notes": "Trial key via Cohere dashboard.",
    },
    {
        "id": "mistral-free",
        "name": "Mistral AI (free / open weights)",
        "provider": "Mistral",
        "description": "Open-weight models (e.g. Mistral 7B, Mixtral) plus a free La Plateforme trial tier.",
        "url": "https://mistral.ai/",
        "access": "signup",
        "kind": "api",
        "notes": "Weights are open; hosted API needs signup.",
    },
    {
        "id": "lmstudio-local",
        "name": "LM Studio (local)",
        "provider": "LM Studio",
        "description": "Desktop app to download and chat with GGUF models locally, with a local server mode.",
        "url": "https://lmstudio.ai/",
        "access": "local",
        "kind": "local",
        "notes": "No cloud API key; runs on your machine.",
    },
    {
        "id": "cloudflare-workers-ai",
        "name": "Cloudflare Workers AI (free tier)",
        "provider": "Cloudflare",
        "description": "Edge inference with a daily free neuron allotment for open models.",
        "url": "https://developers.cloudflare.com/workers-ai/",
        "access": "signup",
        "kind": "api",
        "notes": "Cloudflare account required.",
    },
]


def _fetch_hf_models(limit: int) -> list[dict[str, Any]]:
    params = {
        "sort": "downloads",
        "limit": min(limit, 30),
        "filter": "text-generation",
    }
    r = requests.get(HF_MODELS_URL, params=params, headers=UA, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    data = r.json() or []
    out: list[dict[str, Any]] = []
    for m in data:
        model_id = m.get("modelId") or m.get("id") or ""
        if not model_id:
            continue
        out.append(
            {
                "id": f"hf:{model_id}",
                "name": model_id,
                "provider": "Hugging Face",
                "description": f"Popular open text-generation model on Hugging Face ({m.get('pipeline_tag') or 'text-generation'}).",
                "url": f"https://huggingface.co/{model_id}",
                "access": "open",
                "kind": "model",
                "downloads": m.get("downloads") or 0,
                "likes": m.get("likes") or 0,
                "notes": "Open weights on HF Hub; inference may need local runtime or HF Inference API.",
            }
        )
    return out


def list_free_models(*, limit: int = 30, include_hf: bool = True) -> dict[str, Any]:
    """
    Return curated free-tier tools plus optional HF popular models.
    """
    limit = max(1, min(int(limit or 30), 50))
    curated = list(CURATED_FREE)
    hf: list[dict[str, Any]] = []
    hf_error = None
    if include_hf:
        try:
            hf_limit = max(5, limit - len(curated))
            hf = _fetch_hf_models(hf_limit)
        except Exception as e:
            hf_error = str(e)

    combined = curated + hf
    return {
        "curated": curated,
        "huggingface": hf,
        "items": combined[:limit] if limit < len(combined) else combined,
        "hf_error": hf_error,
        "count": {
            "curated": len(curated),
            "huggingface": len(hf),
            "total": len(curated) + len(hf),
        },
    }


def models_status() -> dict[str, Any]:
    curated_ok = len(CURATED_FREE) > 0
    hf: dict[str, Any]
    try:
        r = requests.get(
            HF_MODELS_URL,
            params={"sort": "downloads", "limit": 1, "filter": "text-generation"},
            headers=UA,
            timeout=8,
        )
        hf = {"ok": r.status_code == 200, "status_code": r.status_code}
    except Exception as e:
        hf = {"ok": False, "message": str(e)}
    return {
        "ok": curated_ok or hf.get("ok"),
        "curated": {"ok": curated_ok, "count": len(CURATED_FREE)},
        "huggingface": hf,
    }
