# Copyright @2023. All rights reserved.
# Authors: luozhuofeng@gmail.com (Zhuofeng Luo)
import dataclasses
import logging
import re
from time import sleep
from typing import Optional

import openai
import requests
from retry.api import retry_call

from class_news import News

# NOTE: chatgpt3.5 has a limit of 4096 tokens, and one Chinese character is about two tokens
_OPENAI_MODEL = 'gpt-3.5-turbo'
_OPENAI_MAX_TOKENS = 300
_OPENAI_TEMPERATUR = 1.0
_OPENAI_PRESENCE_PENALTY = 1.0
_OPENAI_FREQUENCY_PENALTY = 0.5
_OPENAI_ASSISTANT_PROMPT = 'You are a helpful assistant.'
_MAX_CONTENT_CHINESE_CHARS = 1600
_SUMMARIZE_QUESTION_FMT = '请为以下新闻写一篇不含标题的中文摘要：\n\n《{title}》\n{content}'


def init_openai(openai_api_key: str, openai_proxy: Optional[str] = None):
    openai.api_key = openai_api_key
    if openai_proxy:
        openai.proxy = openai_proxy


def _count_chinese_chars(s: str):
    visible_chars = re.sub(r'\s+', '', s, flags=re.UNICODE)
    return len(visible_chars)


def summarize_news_with_gpt(
        news: News,
        retry_times: int = 3,
        delay: float = 25,
) -> Optional[News]:
    content = news.content
    if _count_chinese_chars(content) > _MAX_CONTENT_CHINESE_CHARS:
        logging.warning(
            'The content is too long with {} chinese chars, while we have a limit of {}'.format(
                _count_chinese_chars(content), _MAX_CONTENT_CHINESE_CHARS))
        while _count_chinese_chars(content) > _MAX_CONTENT_CHINESE_CHARS:
            content = content[:len(content) - 1]
            punctuation_index = max(
                content.rfind('。'),
                content.rfind('！'),
                content.rfind('？'),
            )
            if punctuation_index < -1:
                logging.error('Cannot find any punctuation mark, skip!')
            content = content[:(punctuation_index + 1)]
    messages = [
        {
            'role': 'system',
            'content': _OPENAI_ASSISTANT_PROMPT,
        },
        {
            'role':
            'user',
            'content':
            _SUMMARIZE_QUESTION_FMT.format(
                title=news.title,
                content=content,
            ),
        },
    ]
    response = retry_call(
        openai.ChatCompletion.create,
        fargs=[],
        fkwargs=dict(
            model=_OPENAI_MODEL,
            messages=messages,
            temperature=_OPENAI_TEMPERATUR,
            n=1,
            max_tokens=_OPENAI_MAX_TOKENS,
            presence_penalty=_OPENAI_PRESENCE_PENALTY,
            frequency_penalty=_OPENAI_FREQUENCY_PENALTY,
        ),
        exceptions=(openai.OpenAIError, requests.exceptions.RequestException),
        tries=retry_times,
        delay=delay,
    )

    # Actively sleep, because the openai api has a request limit of 3/min
    sleep(delay)

    if len(response.choices) == 0:
        logging.error('No response from openai gpt, the news will be skipped: {}'.format(
            news.title))
        return None
    news_with_summary = dataclasses.replace(news)
    news_with_summary.brief_content = response.choices[0]['message']['content']
    logging.info('Summarized content for {} in {} chinese characters.'.format(
        news.title, _count_chinese_chars(news_with_summary.brief_content)))
    return news_with_summary
