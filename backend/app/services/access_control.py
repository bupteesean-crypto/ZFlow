from typing import Any


def _get_value(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def can_access_project(user: Any, project: Any) -> bool:
    if not user or not project:
        return False
    if _get_value(user, "is_platform_admin"):
        return True
    user_id = _get_value(user, "id")
    if _get_value(project, "owner_user_id") == user_id:
        return True
    user_company = _get_value(user, "company_id")
    if user_company and _get_value(project, "company_id") == user_company:
        return _get_value(project, "visibility") == "company"
    return False


def can_manage_project(user: Any, project: Any) -> bool:
    if not user or not project:
        return False
    if _get_value(user, "is_platform_admin"):
        return True
    return _get_value(project, "owner_user_id") == _get_value(user, "id")
