# Copyright @2023. All rights reserved.
# Authors: luozhuofeng@gmail.com (Zhuofeng Luo)
import json
from pathlib import Path
from typing import List

from class_news import News


def write_news_json(news_list: List[News], news_json_path: Path):
    news_dicts = [news.as_dict() for news in news_list]
    news_json_path.write_text(
        json.dumps(news_dicts, indent=2, sort_keys=True, ensure_ascii=False), encoding='utf-8')


def read_news_json(news_json_path: Path) -> List[News]:
    news_json_text = news_json_path.read_text(encoding='utf-8')
    news_json = json.loads(news_json_text)
    news_list = []
    for news in news_json:
        news_list.append(
            News(
                title=news['title'],
                content=news['content'],
                url=news['url'],
                publish_timestamp=news['publish_timestamp'],
                request_timestamp=news['request_timestamp'],
                comment_count=news.get('comment_count', 0),
                brief_content=news.get('brief_content', ''),
                audio_path=news.get('audio_path', '')))
    return news_list
