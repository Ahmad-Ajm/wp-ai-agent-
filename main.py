from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from agent_handler import AgentHandler

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
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "✅ WP AI Agent with LangChain is running!"}

@app.post("/api")
async def handle_request(request: Request, authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            logger.warning("Authorization header missing or invalid")
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid API key. Provide Bearer token."
            )

        api_key = authorization.split(" ")[1]
        data = await request.json()
        prompt = data.get("prompt", "")
        action = data.get("action", "generate_php")

        if not prompt:
            logger.warning("Prompt is empty")
            raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

        logger.info(f"Received action={action} with prompt length={len(prompt)}")

        agent = AgentHandler(api_key)
        result = agent.process_request(prompt, action)

        return JSONResponse({
            "status": "success",
            "action": action,
            "result": result
        })

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Unexpected error. Please try again."
        )
