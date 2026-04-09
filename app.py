from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import requests
import os

app = FastAPI()

AUTHOR = "Jan Bedan"
TOPIC = "Mini helpdesk pro školní síť"

# Lokální fallback pro domácí testování
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

# Školní server - OpenAI compatible API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemma3:27b")


class AIRequest(BaseModel):
    prompt: str


@app.get("/ping")
def ping():
    return "pong"


@app.get("/status")
def status():
    return {
        "status": "ok",
        "author": AUTHOR,
        "topic": TOPIC,
        "time": datetime.now().isoformat(),
        "openai_configured": bool(OPENAI_API_KEY and OPENAI_BASE_URL)
    }


def ask_openai_compatible(prompt: str) -> str:
    url = f"{OPENAI_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Odpovídej česky stručně, ideálně jednou větou."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 80
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()

    return data["choices"][0]["message"]["content"].strip()


def ask_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"Odpověz česky jednou krátkou větou: {prompt}",
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()

    return data.get("response", "").strip()


@app.post("/ai")
def ai(req: AIRequest):
    try:
        if OPENAI_API_KEY and OPENAI_BASE_URL:
            answer = ask_openai_compatible(req.prompt)
            return {
                "answer": answer,
                "provider": "openai-compatible"
            }

        answer = ask_ollama(req.prompt)
        return {
            "answer": answer,
            "provider": "ollama"
        }

    except Exception as e:
        return {
            "answer": "AI momentálně neodpovídá.",
            "error": str(e)
        }
