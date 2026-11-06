import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from app.tickets.routes import router as tickets_router

HOST = "127.0.0.1"
PORT = 8000

load_dotenv()

app = FastAPI(title="ITSM Agent")
app.include_router(tickets_router)


def create_server_config(port: int = PORT) -> uvicorn.Config:
    return uvicorn.Config(app, host=HOST, port=port)


def run() -> None:
    uvicorn.Server(create_server_config()).run()


if __name__ == "__main__":
    run()
