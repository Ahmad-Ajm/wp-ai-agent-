from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import openai
from pathlib import Path

# إعداد السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# تحميل تعليمات الذكاء الصناعي
try:
    WP_PROMPT_INSTRUCTIONS = Path("wp_prompt.txt").read_text(encoding="utf-8")
except Exception as e:
    logger.error("تعذر تحميل ملف wp_prompt.txt")
    WP_PROMPT_INSTRUCTIONS = ""

# إعداد تطبيق FastAPI
app = FastAPI()

# السماح بالوصول من جميع النطاقات (ينصح بتحديدها في بيئة الإنتاج)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "✅ WP AI Predict server is running."}

@app.post("/predict")
async def predict(request: Request, authorization: str = Header(None)):
    try:
        data = await request.json()
        prompt = data.get("prompt", "").strip()
        api_key = data.get("api_key") or (authorization or "").removeprefix("Bearer ").strip()

        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API key")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")

        openai.api_key = api_key

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": WP_PROMPT_INSTRUCTIONS},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        result = response['choices'][0]['message']['content']

        return JSONResponse({
            "status": "success",
            "result": result
        })

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error during prediction: {e}", exc_info=True)
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)
