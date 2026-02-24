from asyncio import Queue, sleep
from datetime import datetime, timezone
from logging import Logger

from model.memo_store import Memo
from sqlite.engine import SQLiteEngine


class Checker:
    engine: SQLiteEngine
    task_queue: Queue[Memo]
    logger: Logger

    def __init__(self, engine: SQLiteEngine, task_queue: Queue[Memo], logger: Logger):
        self.engine = engine
        self.task_queue = task_queue
        self.logger = logger

    async def start(self):
        while True:
            try:
                self.logger.info("checker started")
                await self.__check_deadline_memo()
            except Exception as e:
                self.logger.error(f"checker error: {str(e)}", exc_info=True)

            # 尽量对齐时间到整点
            now = datetime.now()
            sub = 60 - now.second
            wait = sub if sub <= 30 else 60
            await sleep(wait)

    async def __check_deadline_memo(self):
        now = datetime.now(timezone.utc)
        start, end = self.__get_alert_minute_start_and_end(now)
        memos = await self.engine.query(
            Memo, Memo.alert_at >= start, Memo.alert_at <= end, Memo.done == False
        )
        self.logger.info(f"checker found {len(memos)} memos to alert")
        for memo in memos:
            await self.task_queue.put(memo)

    def __get_alert_minute_start_and_end(
        self, alert_minute: datetime
    ) -> tuple[datetime, datetime]:
        start = datetime(
            year=alert_minute.year,
            month=alert_minute.month,
            day=alert_minute.day,
            hour=alert_minute.hour,
            minute=alert_minute.minute,
            second=0,
            microsecond=0,
            tzinfo=timezone.utc,
        )
        end = datetime(
            year=alert_minute.year,
            month=alert_minute.month,
            day=alert_minute.day,
            hour=alert_minute.hour,
            minute=alert_minute.minute,
            second=59,
            microsecond=999999,
            tzinfo=timezone.utc,
        )
        return start, end
