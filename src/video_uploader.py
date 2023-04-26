# Copyright @2023. All rights reserved.
# Authors: luozhuofeng@gmail.com (Zhuofeng Luo)
import json
from datetime import datetime
from pathlib import Path

import click

from util import setup_logging
from util_bilibili import UtilBilibili

_TITLE_FMT = '《十分热》每日新闻-{date}'
_TAGS = ['新闻', '每日新闻', '时事', '政治', '热点', 'ChatGPT', 'AI']

_CONFIG = {}
with open('config.json', 'r') as f:
    _CONFIG = json.loads(f.read())


@click.group()
def main():
    setup_logging()


@main.command()
@click.option('--video_file', required=True, type=click.Path(dir_okay=False, exists=True))
@click.option('--cover_file', required=True, type=click.Path(dir_okay=False, exists=True))
@click.option('--description_file', required=True, type=click.Path(dir_okay=False, exists=True))
@click.option('--date', default=datetime.now().strftime('%Y%m%d'), type=str)
def upload_to_bilibili(
        video_file: str,
        cover_file: str,
        description_file: str,
        date: str,
):
    UtilBilibili.init(
        sessdata=_CONFIG['bili_sessdata'],
        bili_jct=_CONFIG['bili_jct'],
        buvid3=_CONFIG['bili_buvid3'],
    )
    if not UtilBilibili.check_login():
        raise ValueError('Unavailable bilibili cookies, please update it.')
    description = Path(description_file).read_text()
    UtilBilibili.upload(
        video_file_path=Path(video_file),
        cover_file_path=Path(cover_file),
        title=_TITLE_FMT.format(date=date),
        description=description,
        tags=_TAGS)


if __name__ == '__main__':
    main()
