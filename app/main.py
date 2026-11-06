import uvicorn
from fastapi import FastAPI

HOST = "127.0.0.1"
PORT = 8000

app = FastAPI(title="ITSM Agent")


def create_server_config(port: int = PORT) -> uvicorn.Config:
    return uvicorn.Config(app, host=HOST, port=port)


def run() -> None:
    uvicorn.Server(create_server_config()).run()


if __name__ == "__main__":
    run()
