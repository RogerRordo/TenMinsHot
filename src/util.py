# Copyright @2023. All rights reserved.
# Authors: luozhuofeng@gmail.com (Zhuofeng Luo)
import asyncio
import logging
import re
from typing import Any, Coroutine


def setup_logging(logging_level=logging.INFO):
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter('%(asctime)s [%(filename)s:%(lineno)d] [%(levelname)s] %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging_level)


def _ensure_event_loop() -> None:
    try:
        asyncio.get_event_loop()
    except:  # pylint: disable=bare-except
        asyncio.set_event_loop(asyncio.new_event_loop())


def sync(coroutine: Coroutine) -> Any:
    """Async to sync"""
    _ensure_event_loop()
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)


def count_chinese_chars(txt: str):
    visible_chars = re.sub(r'\s+', '', txt, flags=re.UNICODE)
    return len(visible_chars)
