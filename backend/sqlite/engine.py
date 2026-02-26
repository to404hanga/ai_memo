from typing import Sequence

from sqlmodel import SQLModel, select, delete
from sqlalchemy.sql._typing import _ColumnExpressionArgument
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlmodel import SQLModel, select
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

# 异步 SQLite 必须使用 sqlite+aiosqlite 驱动
DATABASE_URL = "sqlite+aiosqlite:///memo.db"


class SQLiteEngine:
    engine: AsyncEngine

    def __init__(self, models: list[type] = None):
        self.engine = create_async_engine(DATABASE_URL, echo=True)

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def create[T: SQLModel](self, data: T):
        async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            session.add(data)
            await session.commit()
            await session.refresh(data)
            return data

    async def update[T: SQLModel](
        self, data: T, *where_clauses: _ColumnExpressionArgument[bool] | bool
    ):
        async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            # 构建查询
            statement = select(type(data))

            if where_clauses:
                # 如果有 where 条件, 就用 where 条件
                statement = statement.where(*where_clauses)
            else:
                # 否则默认使用主键作为条件

                # 获取主键
                mapper = inspect(type(data))
                primary_keys = mapper.primary_key

                pk_conditions: list[_ColumnExpressionArgument[bool] | bool] = []
                for pk_column in primary_keys:
                    pk_name = pk_column.key
                    pk_value = getattr(data, pk_name)

                    # 检查主键是否有值
                    if pk_value is None:
                        raise ValueError(
                            f"Update operation requires primary key '{pk_name}' to be set."
                        )

                    pk_conditions.append(getattr(type(data), pk_name) == pk_value)

                statement = statement.where(*pk_conditions)

            # 执行查询，查找所有匹配的记录
            result = await session.exec(statement)
            results: Sequence[T] = result.all()

            if not results:
                return

            # 设置修改数据
            update_data = data.model_dump(exclude_unset=True, exclude_none=True)
            for db_record in results:
                for key, value in update_data.items():
                    setattr(db_record, key, value)
                session.add(db_record)

            await session.commit()

    async def query[T: SQLModel](
        self,
        model: type[T],
        *where_clauses: _ColumnExpressionArgument[bool] | bool,
        offset: int = 0,
        limit: int = 10,
    ) -> list[T]:
        async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            statement = select(model).offset(offset).limit(limit)
            if where_clauses:
                statement = statement.where(*where_clauses)

            result = await session.exec(statement)
            results: Sequence[T] = result.all()
            return list(results)

    async def delete[T: SQLModel](
        self, model: type[T], *where_clauses: _ColumnExpressionArgument[bool] | bool
    ):
        async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            statement = delete(model)
            if where_clauses:
                statement = statement.where(*where_clauses)
            await session.exec(statement)
            await session.commit()
