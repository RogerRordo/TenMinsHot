# Copyright @2023. All rights reserved.
# Authors: luozhuofeng@gmail.com (Zhuofeng Luo)
import logging
from typing import Optional

import requests
from retry.api import retry_call

_DEFAULT_HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"  # pylint: disable=line-too-long
}


def _send_request(method: str, url: str, retry_times: int, delay: float, backoff: float,
                  **kargs) -> requests.Response:
    logging.debug('Sending request: {}'.format(
        dict(
            method=method, url=url, retry_times=retry_times, delay=delay, backoff=backoff,
            **kargs)))
    response = retry_call(
        requests.request,
        fargs=[method, url],
        fkwargs=kargs,
        exceptions=(requests.exceptions.RequestException, requests.exceptions.HTTPError),
        tries=retry_times,
        delay=delay,
        backoff=backoff,
    )
    return response


def request_get(
        url: str,
        params: Optional[dict] = None,
        extra_headers: Optional[dict] = None,
        timeout: float = 5,
        retry_times: int = 5,
        delay: float = 1,
        backoff: float = 2,
) -> requests.Response:
    return _send_request(
        method='GET',
        url=url,
        retry_times=retry_times,
        delay=delay,
        backoff=backoff,
        params=params,
        headers={
            **_DEFAULT_HEADERS,
            **(extra_headers or {}),
        },
        timeout=timeout)


def request_post(
        url: str,
        data: Optional[dict] = None,
        extra_headers: Optional[dict] = None,
        timeout: float = 5,
        retry_times: int = 5,
        delay: float = 1,
        backoff: float = 2,
) -> requests.Response:
    return _send_request(
        method='POST',
        url=url,
        retry_times=retry_times,
        delay=delay,
        backoff=backoff,
        data=data,
        headers={
            **_DEFAULT_HEADERS,
            **(extra_headers or {}),
        },
        timeout=timeout)
