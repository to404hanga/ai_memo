from asyncio import Queue
from logging import Logger
from datetime import UTC, datetime, timezone
from sys import platform

from model.memo_store import Memo


class Notifyer:
    task_queue: Queue[Memo]
    logger: Logger
    WORK_TIMEZONE: timezone | None
    platform: str

    def __init__(self, task_queue: Queue[Memo], logger: Logger):
        self.task_queue = task_queue
        self.logger = logger
        self.WORK_TIMEZONE = datetime.now().astimezone().tzinfo
        if self.WORK_TIMEZONE is None:
            self.WORK_TIMEZONE = UTC
        if platform.startswith("win"):
            self.platform = "win"
        elif platform.startswith("darwin"):
            self.platform = "darwin"
        elif platform.startswith("linux"):
            self.platform = "linux"
            raise NotImplementedError("linux platform not supported")
        else:
            raise NotImplementedError(f"unknown platform {platform}")

    async def start(self):
        while True:
            memo = await self.task_queue.get()
            self.logger.info(f"notifyer got memo {memo.title}")
            self.__notify(memo)

    def __notify(self, memo: Memo):
        msg = f"将于 {memo.alert_at.astimezone(self.WORK_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} 截止\n\n{memo.content if len(memo.content) <= 50 else memo.content[:50] + '...'}"
        jump_url = "https://www.baidu.com"
        match self.platform:
            case "win":
                import winotify

                toast = winotify.Notification(
                    app_id="AI Memo",
                    title=memo.title,
                    msg=msg,
                    duration="long",
                )
                # ! 暂未实现查看详情功能
                toast.add_actions(label="查看详情", launch=jump_url)
                toast.set_audio(winotify.audio.Default, loop=False)
                toast.show()
            case "darwin":
                # ! mac osx 暂未测试
                import pync

                pync.Notifier.notify(
                    message=msg,
                    title=memo.title,
                    open=jump_url,
                    sound="Ping",
                    group="AI Memo",
                )
            case "linux":
                raise NotImplementedError("not yet supported for linux")
            case _:
                raise NotImplementedError(f"unknown platform {self.platform}")
