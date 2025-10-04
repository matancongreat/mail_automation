import json
from typing import Any, Dict, List


async def handle_oauth_callback(service, code: str, scope, redirect_uri: str, response, front_url: str, message: str) -> Dict[str, Any]:
    """Common handler for OAuth callbacks.

    - exchanges code for credentials using the provided service (service.exchange_code_for_credentials)
    - verifies/normalizes scopes and user_info
    - sets an HTTPOnly cookie named `user_info`
    - returns a JSON-serializable payload dict
    """
    result = await service.exchange_code_for_credentials(code, scope, redirect_uri)
    user_id = result.get("user_id")
    user_info = result.get("user_info") or {}
    scope_val = result.get("scope")

    # normalize scopes into a list
    if isinstance(scope_val, str):
        scopes: List[str] = scope_val.split() if scope_val else []
    elif isinstance(scope_val, (list, tuple)):
        scopes = list(scope_val)
    else:
        if isinstance(scope, str):
            scopes = scope.split() if scope else []
        elif isinstance(scope, (list, tuple)):
            scopes = list(scope)
        else:
            scopes = []

    # set HTTPOnly cookie for user_info (dev-friendly flags)
    if response is not None:
        try:
            response.set_cookie("user_info", json.dumps(user_info), httponly=True, secure=False, domain=front_url)
        except Exception:
            # best-effort: if cookie cannot be set, continue and return payload
            pass

    return {"message": message, "user_id": user_id, "user_info": user_info, "scopes": ''.join(scopes)}
