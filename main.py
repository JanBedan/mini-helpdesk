import os
from datetime import datetime

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI
import httpx

app = FastAPI(title="Mini Helpdesk")

api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_BASE_URL")


class Prompt(BaseModel):
    prompt: str


def ask_ai_text(user_text: str) -> str:
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        http_client=httpx.Client(verify=False)
    )

    response = client.chat.completions.create(
        model="gemma3:27b",
        messages=[
            {
                "role": "system",
                "content": "Odpovídej česky, stručně a srozumitelně."
            },
            {
                "role": "user",
                "content": user_text
            }
        ]
    )

    return response.choices[0].message.content


def render_page(answer: str = "", prompt: str = "", error: str = "") -> str:
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
                overflow-wrap: anywhere;
            }}
        </style>
    </head>
    <body>
        <div class="box">
            <h1>Mini Helpdesk</h1>
            <p>Zadej dotaz a aplikace ti vrátí stručnou odpověď.</p>

            <form method="post" action="/ask">
                <textarea name="prompt" placeholder="Sem napiš dotaz...">{prompt}</textarea><br>
                <button type="submit">Odeslat dotaz</button>
            </form>

            {"<div class='result'><strong>Odpověď:</strong><br><br>" + answer + "</div>" if answer else ""}
            {"<div class='error'><strong>Chyba:</strong><br><br>" + error + "</div>" if error else ""}
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
        answer = ask_ai_text(prompt)
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
        "author": "Jan Bedan",
        "topic": "Mini helpdesk pro školní síť",
        "time": datetime.now().isoformat()
    }


@app.post("/ai")
def ai(data: Prompt):
    try:
        answer = ask_ai_text(data.prompt)
        return {"answer": answer}
    except Exception as e:
        return {"error": str(e)}
