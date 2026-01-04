from typing import Dict, Optional

from pydantic import BaseModel


class Task(BaseModel):
    id: str
    status: str
    progress: float = 0.0
    result_url: Optional[str] = None
    metadata: Dict[str, str] = {}
