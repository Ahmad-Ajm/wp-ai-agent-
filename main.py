from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import openai

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # عدل هذا لاحقًا إن أردت تخصيصه
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
        
        # استخدام الواجهة الجديدة
        response = openai.chat_completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
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
