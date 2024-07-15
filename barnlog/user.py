from typing import Any

from barnlog.utils import Local

_user_info = Local()


def get_user_info() -> dict[str, Any] | None:
    # return getattr(_django_http_request_context, "value", None)
    if hasattr(_user_info, "value"):
        return _user_info.value
    try:
        from barnlog.django import get_django_user_info
    except ImportError:
        pass
    else:
        return get_django_user_info()


def set_user_info(user_id: Any, username: str, is_authenticated: bool | None = None) -> None:
    _user_info.value = {
        "id": user_id,
        "username": username,
        "is_authenticated": is_authenticated,
    }


def clear_current_user_context() -> None:
    if hasattr(_user_info, "value"):
        del _user_info.value
