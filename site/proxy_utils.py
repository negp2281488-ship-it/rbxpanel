import logging
import random
import requests
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

PROXIES_FILE = "proxies.txt"

_bad_proxies: Set[str] = set()
_bad_proxies_time: dict[str, datetime] = {}
BAD_PROXY_TTL = timedelta(minutes=5)


def load_proxies(proxies_file: str = PROXIES_FILE) -> List[str]:
    proxies = []
    proxies_path = Path(proxies_file)

    if not proxies_path.exists():
        logger.warning(f"Proxies file not found: {proxies_file}")
        return []

    try:
        with open(proxies_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    proxies.append(line)
        logger.info(f"Loaded {len(proxies)} proxies from {proxies_file}")
        return proxies
    except Exception as e:
        logger.error(f"Error loading proxies: {e}")
        return []


def _normalize_proxy(proxy: str) -> str:
    if proxy and "://" not in proxy:
        return "http://" + proxy
    return proxy


def get_random_proxy(proxies: Optional[List[str]] = None) -> Optional[str]:
    if proxies is None:
        proxies = load_proxies()
    if not proxies:
        return None
    return _normalize_proxy(random.choice(proxies))


def check_proxy_health(proxy: str, timeout: int = 5) -> bool:
    try:
        proxy_url = proxy if "://" in proxy else f"http://{proxy}"
        response = requests.get(
            "https://www.google.com",
            proxies={"http": proxy_url, "https": proxy_url},
            timeout=timeout,
            allow_redirects=False
        )
        return True
    except Exception:
        return False


def mark_proxy_bad(proxy: str):
    _bad_proxies.add(proxy)
    _bad_proxies_time[proxy] = datetime.now()
    logger.warning(f"Marked proxy {proxy[:30]}... as bad")


def is_proxy_bad(proxy: str) -> bool:
    if proxy not in _bad_proxies:
        return False
    if proxy in _bad_proxies_time:
        if datetime.now() - _bad_proxies_time[proxy] > BAD_PROXY_TTL:
            _bad_proxies.discard(proxy)
            _bad_proxies_time.pop(proxy, None)
            return False
    return True


def get_random_proxy_safe(proxies: Optional[List[str]] = None, exclude_bad: bool = True) -> Optional[str]:
    if proxies is None:
        proxies = load_proxies()
    if not proxies:
        return None

    if exclude_bad:
        good = [p for p in proxies if not is_proxy_bad(p)]
        pool = good if good else proxies
    else:
        pool = proxies

    return _normalize_proxy(random.choice(pool))
