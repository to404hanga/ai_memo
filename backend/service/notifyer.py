from asyncio import Queue
from logging import Logger

from plyer import notification

from model.memo_store import Memo


class Notifyer:
    task_queue: Queue[Memo]
    logger: Logger

    def __init__(self, task_queue: Queue[Memo], logger: Logger):
        self.task_queue = task_queue
        self.logger = logger

    async def start(self):
        while True:
            memo = await self.task_queue.get()
            self.logger.info(f"notifyer got memo {memo.title}")
            self.__notify(memo)

    def __notify(self, memo: Memo):
        try:
            notification.notify(
                title=memo.title,
                message=f"将于{memo.deadline}截止\n\n{memo.content}",
                app_name="AI Memo",
                timeout=10,
            )
        except Exception as e:
            self.logger.error(f"notifyer error: {e}")
