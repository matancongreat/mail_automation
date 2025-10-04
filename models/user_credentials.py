from typing import List
from pydantic import BaseModel


class UserCredentials(BaseModel):
    token: str
    refresh_token: str
    token_uri: str
    client_id: str
    scopes: List[str]
