from pydantic import BaseModel


class LiveHealthResponse(BaseModel):
    status: str
    app_name: str
    version: str


class ReadyHealthResponse(BaseModel):
    status: str
    dependencies: dict[str, str]
