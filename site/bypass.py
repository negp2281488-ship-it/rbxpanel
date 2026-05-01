import logging
import requests
from typing import Optional, List

logger = logging.getLogger(__name__)


class RobloxBypass:
    def __init__(self, cookie: str, proxy: Optional[dict] = None):
        self.cookie = cookie.strip()
        self.xcsrf_token = None
        self.rbx_authentication_ticket = None
        self.proxy = proxy
        self.session = requests.Session()
        if proxy:
            self.session.proxies.update(proxy)

    def get_csrf_token(self) -> tuple[bool, str]:
        try:
            response = self.session.post(
                "https://auth.roblox.com/v2/logout",
                cookies={".ROBLOSECURITY": self.cookie},
                timeout=10
            )
            self.xcsrf_token = response.headers.get("x-csrf-token")
            if not self.xcsrf_token:
                return False, "Invalid cookie or failed to obtain CSRF token"
            return True, "CSRF token obtained"
        except Exception as e:
            logger.error(f"Bypass CSRF error: {type(e).__name__}")
            return False, f"CSRF error: {type(e).__name__}"

    def get_authentication_ticket(self) -> tuple[bool, str]:
        try:
            response = self.session.post(
                "https://auth.roblox.com/v1/authentication-ticket",
                headers={
                    "rbxauthenticationnegotiation": "1",
                    "referer": "https://www.roblox.com/",
                    "Content-Type": "application/json",
                    "x-csrf-token": self.xcsrf_token
                },
                cookies={".ROBLOSECURITY": self.cookie},
                timeout=10
            )
            self.rbx_authentication_ticket = response.headers.get("rbx-authentication-ticket")
            if not self.rbx_authentication_ticket:
                return False, "Failed to obtain authentication ticket"
            return True, "Authentication ticket obtained"
        except Exception as e:
            logger.error(f"Bypass ticket error: {type(e).__name__}")
            return False, f"Ticket error: {type(e).__name__}"

    def redeem_ticket(self) -> tuple[bool, str]:
        try:
            response = self.session.post(
                "https://auth.roblox.com/v1/authentication-ticket/redeem",
                headers={"rbxauthenticationnegotiation": "1"},
                json={"authenticationTicket": self.rbx_authentication_ticket},
                timeout=10
            )
            set_cookie_header = response.headers.get("set-cookie", "")
            if ".ROBLOSECURITY=" not in set_cookie_header:
                return False, "Failed to obtain new cookie from ticket redeem"

            new_cookie = set_cookie_header.split(".ROBLOSECURITY=")[1].split(";")[0]
            return True, new_cookie
        except Exception as e:
            logger.error(f"Bypass redeem error: {type(e).__name__}")
            return False, f"Redeem error: {type(e).__name__}"

    def run(self) -> tuple[bool, str]:
        try:
            ok, msg = self.get_csrf_token()
            if not ok:
                logger.warning(f"Bypass failed at CSRF: {msg}")
                return False, msg

            ok, msg = self.get_authentication_ticket()
            if not ok:
                logger.warning(f"Bypass failed at ticket: {msg}")
                return False, msg

            ok, result = self.redeem_ticket()
            if not ok:
                logger.warning(f"Bypass failed at redeem: {result}")
                return False, result

            logger.info("Bypass completed successfully")
            return True, result
        finally:
            self.session.close()


def bypass_cookie(
    cookie: str,
    proxy: Optional[dict] = None,
    extra_proxies: Optional[List[str]] = None,
    retries: int = 3,
) -> tuple[bool, str]:
    import random

    # Build candidate list: only proxies, no direct
    proxy_candidates: List[Optional[dict]] = []

    if proxy:
        proxy_candidates.append(proxy)

    if extra_proxies:
        # Pick random proxies for each retry cycle
        sample = random.sample(extra_proxies, min(retries, len(extra_proxies)))
        for p in sample:
            if p:
                normalized = p if "://" in p else f"http://{p}"
                proxy_candidates.append({"http": normalized, "https": normalized})

    if not proxy_candidates:
        # Only if zero proxies available — fallback to direct
        proxy_candidates.append(None)

    last_error = "No attempts made"
    for attempt in range(retries):
        current_proxy = proxy_candidates[attempt % len(proxy_candidates)]
        proxy_label = "direct" if current_proxy is None else "proxy"
        logger.info(f"Bypass attempt {attempt + 1}/{retries}, {proxy_label}")
        ok, result = RobloxBypass(cookie, proxy=current_proxy).run()
        if ok:
            logger.info(f"Bypass success on attempt {attempt + 1}/{retries}, {proxy_label}")
            return True, result
        last_error = result
        logger.warning(f"Bypass attempt {attempt + 1}/{retries} failed ({proxy_label}): {result}")

    return False, last_error
