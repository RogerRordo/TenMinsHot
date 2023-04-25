# Copyright @2023. All rights reserved.
# Authors: luozhuofeng@gmail.com (Zhuofeng Luo)
import dataclasses
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import List, Set

from bs4 import BeautifulSoup

from class_news import News
from util_request import request_get

_PAGE_SIZE = 20
_HOT_RANKING_LIST_URL = 'https://r.inews.qq.com/gw/event/hot_ranking_list'
_MAX_HOURS_DIFF_ALLOWED = 24


def _get_news_list_without_content(news_num: int) -> List[News]:
    news_list_without_content: List[News] = []
    news_id_set: Set[str] = set()
    offset = 0
    ids_hash = ''
    while len(news_list_without_content) < news_num:
        request_time = datetime.now()
        raw_hot_ranking_list_response = request_get(
            url=_HOT_RANKING_LIST_URL,
            params={
                'ids_hash': ids_hash,
                'offset': offset,
                'page_size': _PAGE_SIZE,
            },
            extra_headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            })
        raw_hot_ranking_list_json = raw_hot_ranking_list_response.json()
        offset += _PAGE_SIZE
        ids_hash = raw_hot_ranking_list_json['idlist'][0].get('ids_hash', '')
        raw_hot_ranking_list = raw_hot_ranking_list_json['idlist'][0].get('newslist', [])

        # Filter only article
        raw_hot_ranking_list = list(
            filter(lambda news: news.get('articletype') == '0', raw_hot_ranking_list))

        has_news_added = False
        for raw_news in raw_hot_ranking_list:
            news_id = raw_news.get('id')
            news_title = raw_news.get('title')
            news_url = raw_news.get('url')
            news_publish_time_str = raw_news.get('time')
            news_source_name = raw_news.get('source') or ''
            news_comment_count = raw_news.get('commentNum') or raw_news.get('comments') or 0
            news_image_path = raw_news.get('fimgUrl', {}).get('ExplicitImageUrl') or (raw_news.get(
                'thumbnails_big', []) or [''])[0]
            if any([
                    not news_id,
                    news_id in news_id_set,
                    not news_title,
                    not news_url,
                    not news_publish_time_str,
            ]):
                continue
            news_publish_time = datetime.strptime(news_publish_time_str, '%Y-%m-%d %H:%M:%S')
            if request_time - news_publish_time > timedelta(hours=_MAX_HOURS_DIFF_ALLOWED):
                # Outdated
                continue

            # Replace host
            # E.g. https://view.inews.qq.com/a/20230424A02U1F00?#
            #   -> https://new.qq.com/rain/a/20230424A02U1F00?#
            news_url = news_url.replace('view.inews.qq.com/a/', 'new.qq.com/rain/a/')

            # Add news
            news_id_set.add(news_id)
            news_list_without_content.append(
                News(
                    title=news_title,
                    content='',
                    url=news_url,
                    publish_timestamp=news_publish_time.timestamp(),
                    request_timestamp=request_time.timestamp(),
                    source_name=news_source_name,
                    comment_count=news_comment_count,
                    image_path=news_image_path))
            has_news_added = True

        if not has_news_added:
            # No more news
            break

    # Sort in comments count desc and truncate
    news_list_without_content = sorted(
        news_list_without_content, key=lambda news: news.comment_count, reverse=True)[:news_num]
    logging.info('Got {} news from hot ranking list'.format(len(news_list_without_content)))
    return news_list_without_content


def _parse_news_content_from_html(raw_html: str) -> str:
    beautiful_soup = BeautifulSoup(raw_html, 'html.parser')
    content = beautiful_soup.select('div.LEFT div.content.clearfix')[0].get_text()
    return content


def _fetch_news_content(news_list_without_content: List[News]) -> List[News]:
    news_list: List[News] = []
    for index, news in enumerate(news_list_without_content):
        raw_news_article_response = request_get(url=news.url)
        raw_news_article_html = raw_news_article_response.text
        news_with_content = dataclasses.replace(news)
        news_with_content.content = _parse_news_content_from_html(raw_news_article_html)
        news_list.append(news_with_content)
        logging.info('Got the content of the news: {} [{}/{}]'.format(
            news.title, index + 1, len(news_list_without_content)))
    return news_list


def _fetch_news_image(news_list_without_image: List[News], image_dir_path: Path) -> List[News]:
    news_list: List[News] = []
    for index, news in enumerate(news_list_without_image):
        if not news.image_path:
            logging.warning(
                'There is no cover image for the news {}, skip download its image.'.format(
                    news.title))
            continue
        raw_news_image_response = request_get(url=news.image_path)
        image_extension = raw_news_image_response.headers.get('content-type',
                                                              '').split('/')[-1] or 'webp'
        image_path = image_dir_path / f'{str(index).zfill(2)}.{image_extension}'
        image_path.write_bytes(raw_news_image_response.content)
        news_with_image = dataclasses.replace(news)
        news_with_image.image_path = str(image_path)
        news_list.append(news_with_image)
        logging.info('Downloaded the image of the news: {} [{}/{}] to {}'.format(
            news.title, index + 1, len(news_list_without_image), str(image_path)))
    return news_list


def get_tencent_hot_ranking_list(news_num: int, image_dir_path: Path) -> List[News]:
    news_list_without_content = _get_news_list_without_content(news_num=news_num)
    news_list_without_image = _fetch_news_content(news_list_without_content)
    news_list = _fetch_news_image(news_list_without_image, image_dir_path)
    return news_list
