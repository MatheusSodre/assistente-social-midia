from pydantic import BaseModel


class AgencyChatRequest(BaseModel):
    business_id: str
    message: str
