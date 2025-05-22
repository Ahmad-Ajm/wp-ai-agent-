from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import redis
import os

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

# الاتصال بـ Redis
try:
    redis_host = os.getenv('REDIS_HOST', 'redis://red-d0mb46be5dus738c20kg')  # اسم الخدمة بدلاً من localhost
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

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/predict")
async def predict(request: Request, authorization: str = Header(None)):
    try:
        data = await request.json()
        prompt = data.get("prompt", "").strip()
        session_id = data.get("session_id", "")
        api_key = data.get("api_key") or (authorization or "").removeprefix("Bearer ").strip()
        model = data.get("model", "")

        if not api_key:
            raise HTTPException(status_code=401, detail="مفتاح API مفقود")
        if not prompt:
            raise HTTPException(status_code=400, detail="النص لا يمكن أن يكون فارغًا")
        if not session_id:
            raise HTTPException(status_code=400, detail="معرف الجلسة مطلوب")
        if not model:
            raise HTTPException(status_code=400, detail="نموذج الذكاء الاصطناعي مطلوب")

        # هنا يمكن إضافة منطق المعالجة باستخدام Redis
        return JSONResponse({"status": "success", "result": "تمت المعالجة بنجاح"})

    except HTTPException as he:
        raise he
    except redis.ConnectionError as e:
        logger.error(f"خطأ في الاتصال بـ Redis: {e}")
        return JSONResponse({"status": "error", "message": "فشل في الاتصال بـ Redis"}, status_code=500)
    except Exception as e:
        logger.error(f"خطأ أثناء المعالجة: {e}")
        return JSONResponse({"status": "error", "message": f"فشل في المعالجة: {str(e)}"}, status_code=500)
