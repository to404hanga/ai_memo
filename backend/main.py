from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from router.memo import MemoRouter
from service.memo import MemoService
from sqlite.engine import SQLiteEngine
from model.memo_store import Memo

@asynccontextmanager
async def lifespan(app: FastAPI):
    await engine.init_db()
    yield
    await engine.engine.dispose()

if __name__ == "__main__":
    engine = SQLiteEngine(models=[Memo])

    memo_service = MemoService(engine=engine)
    memo_router = MemoRouter(service=memo_service)

    app = FastAPI(lifespan=lifespan)
    app.include_router(memo_router.router)

    uvicorn.run(app, host="0.0.0.0", port=8000)
