import sys
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.routers import auth, sessions, analysis

# Clear default logger and set clean colored format
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>",
    level="INFO"
)

app = FastAPI(
    title="Talkprint API",
    description="Conversation dynamics analysis backend",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])


@app.on_event("startup")
async def startup():
    logger.info("Talkprint backend is starting up")
    logger.info("Database connection initialized")
    logger.info("Routers registered — auth, sessions, analysis")
    logger.info("Server ready at http://127.0.0.1:8000")


@app.on_event("shutdown")
async def shutdown():
    logger.warning("Talkprint backend is shutting down")


@app.get("/")
def root():
    logger.info("Health check hit")
    return {"status": "Talkprint backend running"}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    logger.info(f"Incoming {request.method} request to {request.url.path}")
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    logger.info(f"Responded with {response.status_code} in {duration}ms")
    return response