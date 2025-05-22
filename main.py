# ✅ الاستيرادات الأساسية من FastAPI
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from agent_handler import AIHandler

# ✅ إعداد تسجيل السجلات (Logs)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ إنشاء تطبيق FastAPI
app = FastAPI()

# ✅ إضافة Middleware لحل مشاكل CORS للسماح بالطلبات من مواقع مختلفة
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # يمكنك تحديد نطاق معين بدلاً من "*" لزيادة الأمان
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ نقطة دخول أساسية لاختبار الخادم
@app.get("/")
def root():
    return {"message": "✅ WP AI Predict server is running."}

# ✅ نقطة فحص الصحة
@app.get("/health")
def health_check():
    return {"status": "ok"}

# ✅ نقطة POST الأساسية للتنبؤ باستخدام الذكاء الصناعي
@app.post("/predict")
async def predict(request: Request, authorization: str = Header(None)):
    try:
        # 🧾 محاولة استخراج البيانات JSON من الجسم
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        # 📌 استخراج البيانات الأساسية
        prompt = data.get("prompt", "").strip()
        session_id = data.get("session_id", "").strip()
        provider = data.get("model", "gpt").strip().lower()
        api_key = (
            data.get("api_key")
            or (authorization or "").removeprefix("Bearer ").strip()
        )

        # ⚠️ التحقق من القيم المطلوبة
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API key")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")

        # ▶️ إنشاء الكائن المناسب لمعالجة الطلب
        handler = AIHandler(provider, api_key)
        result = handler.process_request(prompt, session_id)

        # ✅ إعادة الرد على شكل JSON
        return JSONResponse({
            "status": "success",
            "result": result
        })

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error during prediction: {e}", exc_info=True)
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )
