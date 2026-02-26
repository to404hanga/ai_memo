from datetime import UTC, datetime
from asyncio import (
    CancelledError,
    Queue,
    Task,
    gather,
    create_task,
    wait_for,
    TimeoutError,
)
from contextlib import asynccontextmanager
from logging import INFO, basicConfig, getLogger
from os import getcwd, path as opath
from sys import path as spath

import uvicorn
from fastapi import FastAPI
from langchain.embeddings import init_embeddings
from langchain_community.vectorstores import Chroma


spath.append(opath.abspath(opath.join(opath.dirname(__file__), "../..")))
from agent.rag.ingest import Ingester
from service.notifyer import Notifyer
from service.checker import Checker
from router.memo import MemoRouter
from service.memo import MemoService
from sqlite.engine import SQLiteEngine
from model.memo_store import Memo

WORK_DIR = getcwd()
basicConfig(
    level=INFO,
    filename=f"{WORK_DIR}/memo.log",
    filemode="a",
    encoding="utf-8",
    format="%(asctime)s - %(name)s-%(funcName)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
CHROMA_PATH = f"{WORK_DIR}/chroma_notes"
WORK_TIMEZONE = datetime.now().astimezone().tzinfo
if WORK_TIMEZONE is None:
    WORK_TIMEZONE = UTC

logger = getLogger("AI Memo")
engine = SQLiteEngine(models=[Memo])
task_queue = Queue[Memo]()
embedding_model = init_embeddings(
    model="nomic-embed-text:latest",
    provider="ollama",
)
vector_store = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_model)
ingester = Ingester(embeddings=embedding_model, vectorstore=vector_store)
memo_service = MemoService(engine=engine, ingester=ingester, work_timezone=WORK_TIMEZONE)
memo_router = MemoRouter(service=memo_service)


def task_exception_callback(task: Task):
    try:
        task.result()
    except CancelledError:
        logger.info(f"task {task.get_name()} cancelled")
    except Exception as e:
        logger.error(f"task {task.get_name()} error: {str(e)}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库
    try:
        await engine.init_db()
        logger.info("database initialized")
    except Exception as e:
        logger.error(f"database initialization error: {str(e)}")
        raise

    # 启动后台任务
    checker = Checker(engine=engine, task_queue=task_queue, logger=logger)
    notifyer = Notifyer(task_queue=task_queue, logger=logger, work_timezone=WORK_TIMEZONE)

    checker_task = create_task(checker.start(), name="checker")
    notifyer_task = create_task(notifyer.start(), name="notifyer")

    # 设置任务异常回调
    checker_task.add_done_callback(task_exception_callback)
    notifyer_task.add_done_callback(task_exception_callback)

    logger.info("background (Checker/Notifyer) tasks started")
    yield
    logger.info("background (Checker/Notifyer) tasks stopped")

    # 取消后台任务
    checker_task.cancel()
    notifyer_task.cancel()

    try:
        await wait_for(gather(checker_task, notifyer_task), timeout=5.0)
    except TimeoutError:
        logger.error("background (Checker/Notifyer) tasks timeout")
    except CancelledError:
        logger.info("background (Checker/Notifyer) tasks cancelled")

    await engine.engine.dispose()


if __name__ == "__main__":
    app = FastAPI(lifespan=lifespan)
    app.include_router(memo_router.router)

    uvicorn.run(app, host="0.0.0.0", port=8000)
