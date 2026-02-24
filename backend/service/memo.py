from datetime import datetime, timezone

from sqlalchemy.sql._typing import _ColumnExpressionArgument

from model.memo_store import Memo
from sqlite.engine import SQLiteEngine


class MemoService:
    engine: SQLiteEngine

    def __init__(self, engine: SQLiteEngine):
        self.engine = engine

    async def create_memo(
        self,
        title: str,
        deadline: datetime,
        alert_at: datetime,
        is_urgent: bool,
        content: str = "",
    ):
        memo = Memo(
            title=title,
            content=content,
            deadline=deadline,
            alert_at=alert_at,
            is_urgent=is_urgent,
        )
        await self.engine.create(memo)

    async def update_memo(
        self,
        id: int,
        title: str | None = None,
        content: str | None = None,
        deadline: datetime | None = None,
        alert_at: datetime | None = None,
        is_urgent: bool | None = None,
        done: bool | None = None,
    ):
        memo = Memo(
            id=id,
            title=title,
            content=content,
            deadline=deadline,
            alert_at=alert_at,
            is_urgent=is_urgent,
            done=done,
        )
        await self.engine.update(memo)

    async def delete_memo(self, id: int):
        await self.engine.delete(Memo, Memo.id == id)

    async def get_memo_list(
        self,
        deadline_day: datetime | None = None,
        done: bool | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> list[Memo]:
        query: list[_ColumnExpressionArgument[bool] | bool] = []
        if done is not None:
            query.append(Memo.done == done)
        if deadline_day:
            start, end = self.__get_day_start_and_end(deadline_day)
            query.append(Memo.deadline >= start)
            query.append(Memo.deadline <= end)

        offset = (page - 1) * page_size
        limit = page_size
        memos = await self.engine.query(Memo, *query, offset=offset, limit=limit)
        return memos

    def __get_day_start_and_end(
        self, day: datetime
    ) -> tuple[datetime, datetime]: 
        start = datetime(
            year=day.year,
            month=day.month,
            day=day.day,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
            tzinfo=timezone.utc,
        )
        end = datetime(
            year=day.year,
            month=day.month,
            day=day.day,
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
            tzinfo=timezone.utc,
        )
        return start, end
