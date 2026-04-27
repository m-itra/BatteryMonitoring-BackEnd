from contextlib import asynccontextmanager
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.grpc_server import serve as serve_grpc
from app.routes import admin, auth, health

grpc_thread: threading.Thread | None = None


def start_grpc_server():
    serve_grpc()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global grpc_thread
    if grpc_thread is None or not grpc_thread.is_alive():
        grpc_thread = threading.Thread(target=start_grpc_server, daemon=True)
        grpc_thread.start()

    yield


app = FastAPI(title="UserService", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(health.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
