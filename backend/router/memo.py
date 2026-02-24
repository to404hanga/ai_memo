from datetime import datetime, timezone

from fastapi import APIRouter

from model.memo_service import CreateMemoRequest, UpdateMemoRequest
from service.memo import MemoService
from model.memo_store import Memo


class MemoRouter:
    router: APIRouter
    service: MemoService

    def __init__(self, service: MemoService):
        self.router = APIRouter()
        self.service = service

        self.setup_routes()

    def setup_routes(self):
        self.router.add_api_route(
            "/memo",
            self.create_memo,
            methods=["POST"],
        )
        self.router.add_api_route(
            "/memo/{id}",
            self.update_memo,
            methods=["PUT"],
        )
        self.router.add_api_route(
            "/memo/{id}",
            self.delete_memo,
            methods=["DELETE"],
        )
        self.router.add_api_route(
            "/memo",
            self.get_memo_list,
            methods=["GET"],
        )

    async def create_memo(self, req: CreateMemoRequest):
        if req.alert_at is None:
            req.alert_at = req.deadline
        await self.service.create_memo(
            **req.model_dump(),
        )

    async def update_memo(self, id: int, req: UpdateMemoRequest):
        await self.service.update_memo(
            id=id,
            **req.model_dump(exclude=["id"]),
        )

    async def delete_memo(self, id: int):
        await self.service.delete_memo(id)

    async def get_memo_list(
        self,
        deadline_day: datetime | None = None,
        done: bool | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> list[Memo]:
        # 统一时间为 UTC
        if deadline_day:
            deadline_day = deadline_day.astimezone(timezone.utc)

        memos = await self.service.get_memo_list(
            deadline_day=deadline_day,
            done=done,
            page=page,
            page_size=page_size,
        )
        return memos
