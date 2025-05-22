from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import redis
from agent_handler import DirectOpenAIHandler
import os

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# إعداد CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# اختبار الاتصال بـ Redis عند بدء التطبيق
try:
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    r.ping()
    logger.info("✅ اتصال Redis ناجح")
except redis.ConnectionError as e:
    logger.error(f"❌ فشل الاتصال بـ Redis: {e}")
    raise SystemExit("فشل الاتصال بـ Redis، يرجى التحقق من التكوين.")

@app.get("/")
def root():
    return {"message": "✅ WP AI Predict server is running."}

# مسار للتحقق من الصحة
@app.get("/health")
def health_check():
    return {"status": "ok"}

# مسار المعالجة الرئيسي
@app.post("/predict")
async def predict(request: Request, authorization: str = Header(None)):
    try:
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="جسم الطلب غير صالح (Invalid JSON)")

        prompt = data.get("prompt", "").strip()
        session_id = data.get("session_id", "")
        api_key = data.get("api_key") or (authorization or "").removeprefix("Bearer ").strip()
        model = data.get("model", "")

        # التحقق من البيانات المطلوبة
        if not api_key:
            raise HTTPException(status_code=401, detail="مفتاح API مفقود")
        if not prompt:
            raise HTTPException(status_code=400, detail="النص (prompt) لا يمكن أن يكون فارغًا")
        if not session_id:
            raise HTTPException(status_code=400, detail="معرف الجلسة (session_id) مطلوب")
        if not model:
            raise HTTPException(status_code=400, detail="نموذج الذكاء الاصطناعي (model) مطلوب")

        # معالجة الطلب
        handler = DirectOpenAIHandler(api_key)
        result = handler.process_request(prompt, session_id)

        return JSONResponse({"status": "success", "result": result})

    except HTTPException as he:
        raise he
    except redis.ConnectionError as e:
        logger.error(f"خطأ في الاتصال بـ Redis: {e}")
        return JSONResponse({"status": "error", "message": "فشل في الاتصال بـ Redis"}, status_code=500)
    except Exception as e:
        logger.error(f"خطأ أثناء المعالجة: {e}", exc_info=True)
        return JSONResponse({"status": "error", "message": f"فشل في المعالجة: {str(e)}"}, status_code=500)
