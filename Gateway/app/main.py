from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import admin, analytics, auth, battery, health
from app.utils.proxy_request import close_proxy_client


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await close_proxy_client()


app = FastAPI(title="Battery Monitoring API Gateway", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, tags=["Auth"])
app.include_router(battery.router, tags=["Battery"])
app.include_router(analytics.router, tags=["Analytics"])
app.include_router(admin.router, tags=["Admin"])
app.include_router(health.router, tags=["Health"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
