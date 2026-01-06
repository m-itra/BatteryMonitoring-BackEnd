from fastapi import FastAPI
import threading
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, health
from app.grpc_server import serve as serve_grpc

app = FastAPI(title="UserService", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def start_grpc_server():
    """Запуск gRPC сервера в отдельном потоке"""
    serve_grpc()

app.include_router(auth.router)
app.include_router(health.router)

if __name__ == "__main__":
    import uvicorn
    grpc_thread = threading.Thread(target=start_grpc_server, daemon=True)
    grpc_thread.start()

    uvicorn.run(app, host="0.0.0.0", port=8001)
