from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Memo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deadline: datetime
    alert_at: datetime
    is_urgent: bool = False
    done: bool = False
