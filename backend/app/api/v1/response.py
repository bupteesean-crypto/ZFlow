from typing import Any, Dict


def ok(data: Any) -> Dict[str, Any]:
    return {"code": 0, "message": "success", "data": data}


def fail(code: int, message: str) -> Dict[str, Any]:
    return {"code": code, "message": message, "data": None}
