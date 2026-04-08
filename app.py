from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import requests
import os

app = FastAPI()

AUTHOR = "Jan Bedan"
TOPIC = "Mini helpdesk pro školní síť"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

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
        "time": datetime.now().isoformat()
    }

@app.post("/ai")
def ai(req: AIRequest):
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": f"Odpověz česky jednou krátkou větou: {req.prompt}",
            "stream": False
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        return {
            "answer": data.get("response", "").strip()
        }
    except Exception as e:
        return {
            "answer": "LLM momentálně neodpovídá.",
            "error": str(e)
        }
