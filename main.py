from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
import openai

app = FastAPI()

@app.get("/")
def root():
    return {"message": "✅ WP AI Agent with GPT is running!"}

@app.post("/api")
async def handle_request(request: Request, authorization: str = Header(None)):
    data = await request.json()
    prompt = data.get("prompt", "")
    action = data.get("action", "generate_php")

    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse({"status": "error", "message": "Missing or invalid API key"}, status_code=401)

    openai.api_key = authorization.split(" ")[1]

    system_prompt = (
        "أنت مساعد ذكي لووردبريس. عندما يُطلب منك إنشاء صفحة أو كود PHP، قم بإنتاج كود نظيف وآمن "
        "متوافق مع معايير ووردبريس، واحرص على عدم إضافة شرح، فقط الكود النهائي المطلوب."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        gpt_output = response['choices'][0]['message']['content']
        return JSONResponse({
            "status": "success",
            "generated_php": gpt_output
        })

    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)