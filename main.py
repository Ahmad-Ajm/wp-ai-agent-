from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
import openai
from openai import OpenAI
import os

app = FastAPI()

@app.get("/")
def root():
    return {"message": "✅ WP AI Agent with GPT (v1) is running!"}

@app.post("/api")
async def handle_request(request: Request, authorization: str = Header(None)):
    data = await request.json()
    prompt = data.get("prompt", "")
    action = data.get("action", "generate_php")

    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse({"status": "error", "message": "Missing or invalid API key"}, status_code=401)

    api_key = authorization.split(" ")[1]
    client = OpenAI(api_key=api_key)

    system_prompt = (
        "أنت مساعد ذكي لووردبريس. عندما يُطلب منك إنشاء صفحة أو كود PHP، قم بإنتاج كود نظيف وآمن "
        "متوافق مع معايير ووردبريس. لا تشرح، فقط أعد الكود المطلوب."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        gpt_output = response.choices[0].message.content
        return JSONResponse({
            "status": "success",
            "generated_php": gpt_output
        })

    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)