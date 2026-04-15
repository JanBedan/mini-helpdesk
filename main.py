import os
from datetime import datetime

import httpx
import redis
import uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from openai import OpenAI
from pydantic import BaseModel

app = FastAPI(title="Mini Helpdesk")


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
PORT = int(os.environ.get("PORT", 5000))


class Prompt(BaseModel):
    prompt: str


def get_redis():
    # Redis může startovat o něco déle než app
    for _ in range(10):
        try:
            r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
            r.ping()
            return r
        except Exception:
            import time
            time.sleep(2)
    return None


def ask_ai_text(user_text: str) -> str:
    if not OPENAI_API_KEY:
        raise Exception("Chybí OPENAI_API_KEY v proměnných prostředí.")

    if not OPENAI_BASE_URL:
        raise Exception("Chybí OPENAI_BASE_URL v proměnných prostředí.")

    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
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

    return response.choices[0].message.content or ""


def render_page(answer: str = "", prompt: str = "", error: str = "", counter: int = 0) -> str:
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
                max-width: 850px;
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
                min-height: 140px;
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
            .info {{
                margin-top: 18px;
                padding: 12px;
                background: #f1f5f9;
                border-radius: 8px;
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

            <div class="info">
                <strong>Počet zpracovaných dotazů:</strong> {counter}
            </div>

            {"<div class='result'><strong>Odpověď:</strong><br><br>" + answer + "</div>" if answer else ""}
            {"<div class='error'><strong>Chyba:</strong><br><br>" + error + "</div>" if error else ""}
        </div>
    </body>
    </html>
    """


@app.get("/", response_class=HTMLResponse)
def home():
    r = get_redis()
    counter = 0

    if r:
        try:
            counter = int(r.get("question_count") or 0)
        except Exception:
            counter = 0

    return render_page(counter=counter)


@app.post("/ask", response_class=HTMLResponse)
def ask_form(prompt: str = Form(...)):
    r = get_redis()
    counter = 0

    try:
        answer = ask_ai_text(prompt)

        if r:
            try:
                counter = r.incr("question_count")
                r.set("last_prompt", prompt)
                r.set("last_answer", answer)
            except Exception:
                pass

        return render_page(answer=answer, prompt=prompt, counter=counter)

    except Exception as e:
        if r:
            try:
                counter = int(r.get("question_count") or 0)
            except Exception:
                counter = 0

        return render_page(prompt=prompt, error=str(e), counter=counter)


@app.get("/ping")
def ping():
    return {"ping": "pong"}


@app.get("/status")
def status():
    r = get_redis()
    redis_ok = False
    counter = 0

    if r:
        try:
            redis_ok = r.ping()
            counter = int(r.get("question_count") or 0)
        except Exception:
            redis_ok = False

    return {
        "status": "ok",
        "author": "Jan Bedan",
        "topic": "Mini helpdesk pro školní síť",
        "time": datetime.now().isoformat(),
        "redis_connected": bool(redis_ok),
        "question_count": counter,
        "openai_base_url_set": bool(OPENAI_BASE_URL),
        "openai_api_key_set": bool(OPENAI_API_KEY),
    }


@app.post("/ai")
def ai(data: Prompt):
    try:
        answer = ask_ai_text(data.prompt)

        r = get_redis()
        if r:
            try:
                r.incr("question_count")
                r.set("last_prompt", data.prompt)
                r.set("last_answer", answer)
            except Exception:
                pass

        return {"answer": answer}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
