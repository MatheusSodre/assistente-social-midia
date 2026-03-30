from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class ConnectTokenResponse(BaseModel):
    connect_token: str


class ConnectionCreate(BaseModel):
    item_id: str
    connector_name: Optional[str] = None


class ConnectionOut(BaseModel):
    id: str
    item_id: str
    connector_name: Optional[str]
    status: str
    last_synced_at: Optional[datetime]
    created_at: datetime


class TransactionOut(BaseModel):
    id: str
    connection_id: str
    pluggy_id: Optional[str]
    account_id: Optional[str]
    date: Optional[date]
    description: Optional[str]
    amount: Optional[Decimal]
    type: Optional[str]
    category: Optional[str]
    status: str


class AnalysisOut(BaseModel):
    summary: str
    top_categories: list[dict]
    insights: list[str]
    recommendations: list[str]


class AlertOut(BaseModel):
    id: str
    description: str
    amount: Optional[Decimal]
    date: Optional[date]
    days_until_due: int
    account_id: Optional[str]
