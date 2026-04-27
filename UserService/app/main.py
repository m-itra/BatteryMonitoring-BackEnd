import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.grpc_server import serve as serve_grpc
from app.routes import admin, auth, health

app = FastAPI(title="UserService", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

grpc_thread: threading.Thread | None = None


def start_grpc_server():
    serve_grpc()


app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(health.router)


@app.on_event("startup")
def startup_event():
    global grpc_thread
    if grpc_thread is not None and grpc_thread.is_alive():
        return

    grpc_thread = threading.Thread(target=start_grpc_server, daemon=True)
    grpc_thread.start()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
