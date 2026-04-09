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
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemma3:27b")


class AIRequest(BaseModel):
    prompt: str


def ask_school_ai(prompt: str) -> str:
    url = f"{OPENAI_BASE_URL}/chat"  # 🔥 správný endpoint

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENAI_MODEL,
        "message": prompt   # 🔥 POZOR – není "messages", ale "message"
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

    # univerzální parsování
    if isinstance(data, dict):
        if "response" in data:
            return data["response"]
        if "answer" in data:
            return data["answer"]
        if "content" in data:
            return data["content"]

    return str(data)


def render_page(answer: str = "", prompt: str = "", error: str = "") -> str:
    safe_answer = html.escape(answer)
    safe_prompt = html.escape(prompt)
    safe_error = html.escape(error)

    return f"""
    <!DOCTYPE html>
    <html lang="cs">
    <head>
        <meta charset="UTF-8">
        <title>Mini Helpdesk</title>
        <style>
            body {{
                font-family: Arial;
                max-width: 800px;
                margin: 40px auto;
                background: #f5f5f5;
            }}
            .box {{
                background: white;
                padding: 20px;
                border-radius: 10px;
            }}
            textarea {{
                width: 100%;
                height: 120px;
            }}
            button {{
                margin-top: 10px;
                padding: 10px;
                background: blue;
                color: white;
                border: none;
            }}
            .result {{
                margin-top: 20px;
                background: #eee;
                padding: 10px;
            }}
            .error {{
                margin-top: 20px;
                background: #ffdddd;
                padding: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="box">
            <h1>Mini Helpdesk</h1>

            <form method="post" action="/ask">
                <textarea name="prompt">{safe_prompt}</textarea>
                <br>
                <button type="submit">Odeslat dotaz</button>
            </form>

            {f'<div class="result">{safe_answer}</div>' if safe_answer else ''}
            {f'<div class="error">{safe_error}</div>' if safe_error else ''}
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
        answer = ask_school_ai(prompt)
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
        return {
            "answer": ask_school_ai(req.prompt)
        }
    except Exception as e:
        return {
            "error": str(e)
        }
