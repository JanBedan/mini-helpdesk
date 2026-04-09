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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://kurin.ithope.eu/v1").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemma3:27b")


class AIRequest(BaseModel):
    prompt: str


def ask_ai(prompt: str) -> str:
    url = f"{OPENAI_BASE_URL}/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=60,
        verify=False
    )

    response.raise_for_status()
    data = response.json()

    return data["choices"][0]["message"]["content"]


def render_page(answer="", prompt="", error=""):
    return f"""
    <html>
    <body style="font-family: Arial; max-width:800px; margin:40px auto;">
        <h1>Mini Helpdesk</h1>

        <form method="post" action="/ask">
            <textarea name="prompt" style="width:100%;height:120px;">{html.escape(prompt)}</textarea><br>
            <button>Odeslat dotaz</button>
        </form>

        {"<div style='margin-top:20px;background:#eee;padding:10px;'>" + html.escape(answer) + "</div>" if answer else ""}
        {"<div style='margin-top:20px;background:#ffdddd;padding:10px;'>" + html.escape(error) + "</div>" if error else ""}
    </body>
    </html>
    """


@app.get("/", response_class=HTMLResponse)
def home():
    return render_page()


@app.post("/ask", response_class=HTMLResponse)
def ask_form(prompt: str = Form(...)):
    try:
        answer = ask_ai(prompt)
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
        "time": datetime.now().isoformat()
    }


@app.post("/ai")
def ai(req: AIRequest):
    try:
        return {"answer": ask_ai(req.prompt)}
    except Exception as e:
        return {"error": str(e)}
