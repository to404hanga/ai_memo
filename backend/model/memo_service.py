from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class CreateMemoRequest(BaseModel):
    title: str = Field(max_length=255, min_length=1)
    content: str | None = Field(default=None, max_length=1000)
    alert_at: datetime
    is_urgent: bool = False

    @field_validator("alert_at")
    @classmethod
    def validate_and_convert_alert_at(cls, v: datetime) -> datetime:
        v_utc = v.astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        if v_utc <= now:
            raise ValueError("alert_at must be a future time")
        return v_utc


class UpdateMemoRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255, min_length=1)
    content: str | None = Field(default=None, max_length=1000)
    alert_at: datetime | None = None
    is_urgent: bool | None = None
    done: bool | None = None

    @field_validator("alert_at")
    @classmethod
    def validate_and_convert_alert_at(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return None
        v_utc = v.astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        if v_utc <= now:
            raise ValueError("alert_at must be a future time")
        return v_utc
