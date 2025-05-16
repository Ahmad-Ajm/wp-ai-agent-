from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from agent_handler import AgentHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "✅ WP AI Agent with LangChain is running!"}

@app.post("/api")
async def handle_request(request: Request, authorization: str = Header(None)):
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        action = data.get("action", "generate_php")
        api_key = data.get("api_key") or (authorization.split(" ")[1] if authorization and authorization.startswith("Bearer ") else None)

        if not api_key:
            logger.warning("API key not provided")
            raise HTTPException(status_code=401, detail="Missing OpenAI API key")

        if not prompt:
            logger.warning("Empty prompt received")
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")

        logger.info(f"Processing request: action={action}, prompt_length={len(prompt)}")

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
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)
