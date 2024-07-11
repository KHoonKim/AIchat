import os
import logging

from fastapi import FastAPI, Request
from supabase import create_client, Client
from app.routes.users import router as users_router
from fastapi.middleware.cors import CORSMiddleware






app = FastAPI()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Supabase 클라이언트 초기화
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

supabase: Client = create_client(supabase_url, supabase_key)

# Supabase 클라이언트를 앱 상태로 추가
app.state.supabase = supabase

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request path: {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status code: {response.status_code}")
    return response

# app.include_router(users_router, prefix="")  # prefix를 빈 문자열로 설정


app.include_router(users_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))