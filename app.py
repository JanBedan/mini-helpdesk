from fastapi import FastAPI, Form
from pydantic import BaseModel
from datetime import datetime
from fastapi.responses import HTMLResponse
import requests
import os
import html
import urllib3

app = FastAPI()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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


def try_request(url: str, payload: dict, headers: dict) -> dict:
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=60,
        verify=False
    )
    response.raise_for_status()
    return response.json()


def extract_answer(data: dict) -> str:
    if "choices" in data and len(data["choices"]) > 0:
        choice = data["choices"][0]

        if "message" in choice and "content" in choice["message"]:
            return choice["message"]["content"].strip()

        if "text" in choice:
            return choice["text"].strip()

    if "response" in data:
        return str(data["response"]).strip()

    return str(data)


def ask_openai_compatible(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    errors = []

    # Varianta 1: chat/completions na zadané base URL
    chat_payload = {
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
        "max_tokens": 120
    }

    # Varianta 2: completions na zadané base URL
    completions_payload = {
        "model": OPENAI_MODEL,
        "prompt": f"Odpověz česky stručně, ideálně jednou větou: {prompt}",
        "temperature": 0.3,
        "max_tokens": 120
    }

    urls_to_try = [
        (f"{OPENAI_BASE_URL}/chat/completions", chat_payload),
        (f"{OPENAI_BASE_URL}/completions", completions_payload),
    ]

    # Když by base URL už obsahovala /v1 a server to chtěl bez něj, zkus i to
    if OPENAI_BASE_URL.endswith("/v1"):
        base_without_v1 = OPENAI_BASE_URL[:-3]
        urls_to_try.extend([
            (f"{base_without_v1}/chat/completions", chat_payload),
            (f"{base_without_v1}/completions", completions_payload),
        ])

    for url, payload in urls_to_try:
        try:
            data = try_request(url, payload, headers)
            return extract_answer(data)
        except Exception as e:
            errors.append(f"{url} -> {str(e)}")

    raise Exception(" | ".join(errors))


def ask_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"Odpověz česky stručně, ideálně jednou větou: {prompt}",
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()


def get_ai_answer(prompt: str) -> tuple[str, str]:
    if OPENAI_API_KEY and OPENAI_BASE_URL:
        return ask_openai_compatible(prompt), "openai-compatible"

    return ask_ollama(prompt), "ollama"


def render_page(answer: str = "", prompt: str = "", error: str = "") -> str:
    safe_answer = html.escape(answer)
    safe_prompt = html.escape(prompt)
    safe_error = html.escape(error)

    return f"""
    <!DOCTYPE html>
    <html lang="cs">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mini Helpdesk</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 40px auto;
                padding: 20px;
                background: #f5f5f5;
                color: #222;
            }}
            .box {{
                background: white;
                padding: 24px;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            }}
            h1 {{
                margin-top: 0;
            }}
            textarea {{
                width: 100%;
                min-height: 120px;
                padding: 12px;
                font-size: 16px;
                border: 1px solid #ccc;
                border-radius: 8px;
                box-sizing: border-box;
            }}
            button {{
                margin-top: 12px;
                padding: 12px 18px;
                font-size: 16px;
                border: none;
                border-radius: 8px;
                background: #2563eb;
                color: white;
                cursor: pointer;
            }}
            button:hover {{
                background: #1d4ed8;
            }}
            .result {{
                margin-top: 24px;
                padding: 16px;
                background: #f8fafc;
                border-left: 4px solid #2563eb;
                border-radius: 8px;
                white-space: pre-wrap;
            }}
            .error {{
                margin-top: 24px;
                padding: 16px;
                background: #fef2f2;
                border-left: 4px solid #dc2626;
                border-radius: 8px;
                color: #991b1b;
                white-space: pre-wrap;
            }}
            .info {{
                margin-bottom: 20px;
                color: #555;
            }}
            .small {{
                margin-top: 10px;
                font-size: 14px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="box">
            <h1>Mini Helpdesk</h1>
            <p class="info">
                Jednoduchá AI aplikace pro školní projekt. Zadej dotaz a klikni na tlačítko.
            </p>

            <form method="post" action="/ask">
                <textarea name="prompt" placeholder="Sem napiš dotaz...">{safe_prompt}</textarea>
                <br>
                <button type="submit">Odeslat dotaz</button>
            </form>

            <div class="small">
                Dostupné endpointy: /ping, /status, /ai
            </div>

            {f'<div class="result"><strong>Odpověď:</strong><br><br>{safe_answer}</div>' if safe_answer else ''}
            {f'<div class="error"><strong>Chyba:</strong><br><br>{safe_error}</div>' if safe_error else ''}
        </div>
    </body>
    </html>
    """


@app.get("/", response_class=HTMLResponse)
def home():
    return render_page()


@app.post("/ask", response_class=HTMLResponse)
def ask_form(prompt: str = Form(...)):
    try:
        answer, _provider = get_ai_answer(prompt)
        return render_page(answer=answer, prompt=prompt)
    except Exception as e:
        return render_page(prompt=prompt, error=str(e))


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
        "openai_configured": bool(OPENAI_API_KEY and OPENAI_BASE_URL),
        "openai_base_url": OPENAI_BASE_URL,
        "openai_model": OPENAI_MODEL
    }


@app.post("/ai")
def ai(req: AIRequest):
    try:
        answer, provider = get_ai_answer(req.prompt)
        return {
            "answer": answer,
            "provider": provider
        }
    except Exception as e:
        return {
            "answer": "AI momentálně neodpovídá.",
            "error": str(e)
        }
