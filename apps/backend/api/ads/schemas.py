from pydantic import BaseModel
from typing import Optional


class AdsAccountConnect(BaseModel):
    business_id: str
    customer_id: str
    refresh_token: str
    login_customer_id: Optional[str] = None
    is_test_account: bool = True


class LunaChatRequest(BaseModel):
    business_id: str
    message: str
