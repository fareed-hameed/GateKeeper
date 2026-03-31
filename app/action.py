import requests


def trigger_action(url: str, method: str = "GET", timeout: int = 10) -> dict:
    """Call the protected action URL and return the result.

    Returns {"success": bool, "response": <json or text>, "error": str|None}
    """
    try:
        if method.upper() == "POST":
            resp = requests.post(url, timeout=timeout)
        else:
            resp = requests.get(url, timeout=timeout)

        try:
            body = resp.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            body = resp.text

        return {
            "success": resp.ok,
            "status_code": resp.status_code,
            "response": body,
            "error": None,
        }
    except requests.Timeout:
        return {"success": False, "status_code": None, "response": None, "error": "Action timed out"}
    except requests.ConnectionError:
        return {"success": False, "status_code": None, "response": None, "error": "Action unavailable"}
    except requests.RequestException:
        return {"success": False, "status_code": None, "response": None, "error": "Action failed"}
