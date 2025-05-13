from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os

app = FastAPI()

@app.get("/")
def root():
    return {"message": "✅ WP AI Agent is running!"}

@app.post("/api")
async def handle_request(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    action = data.get("action", "none")

    # استجابة تجريبية
    return JSONResponse({
        "status": "success",
        "action_received": action,
        "prompt_received": prompt
    })