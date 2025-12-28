from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import devices, cycles, analytics, health

app = FastAPI(title="AnalyticsService", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роуты
app.include_router(devices.router)
app.include_router(cycles.router)
app.include_router(analytics.router)
app.include_router(health.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
