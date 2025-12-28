from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, health, analytics_service_route

app = FastAPI(title="UserService", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(analytics_service_route.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
