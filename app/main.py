import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client, create_client

import redis

from app.config import redis_client
from app.routes.characters import router as characters_router
from app.routes.conversations import router as conversations_router
from app.routes.users import router as users_router
# from app.routes.scenarios import router as scenarios_router
from app.services.auth_service import router as auth_router

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application is starting up")
    from app.config import test_redis_connection
    
    if test_redis_connection():
        logger.info("Successfully connected to Redis")
    else:
        logger.warning("Continuing without Redis connection")
    
    yield
    
    try:
        redis_client.close()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")
    logger.info("Application is shutting down")

app = FastAPI(debug=True, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 오리진을 지정해야 합니다
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase: Client = create_client(supabase_url, supabase_key)
app.state.supabase = supabase

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request path: {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status code: {response.status_code}")
    return response

app.include_router(users_router)
app.include_router(characters_router)
app.include_router(conversations_router)
# app.include_router(scenarios_router)
app.include_router(auth_router, prefix="/auth")

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)


