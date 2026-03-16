from pydantic import BaseModel
from datetime import datetime


class SchedulePostRequest(BaseModel):
    draft_id: str
    scheduled_for: datetime
