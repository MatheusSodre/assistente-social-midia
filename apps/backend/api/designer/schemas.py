from pydantic import BaseModel

class DesignerChatResponse(BaseModel):
    response: str
    image_url: str | None = None
    message_count: int

class VisualIdentity(BaseModel):
    primary_color: str = "#000000"
    secondary_color: str = "#FFFFFF"
    accent_color: str = "#FF6B35"
    background_color: str = "#FFFFFF"
    text_color: str = "#000000"
    font_heading: str = "Arial Bold"
    font_body: str = "Arial"
    style_description: str | None = None
    logo_url: str | None = None
    extra_context: str | None = None
