import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import funds, strategies, signals

app = FastAPI(title="黄金ETF量化投资平台", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(funds.router)
app.include_router(strategies.router)
app.include_router(signals.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"message": "黄金ETF量化投资平台 API", "version": "1.0.0"}


@app.get("/api/health")
def health():
    return {"status": "ok"}
