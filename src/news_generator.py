# Copyright @2023. All rights reserved.
# Authors: luozhuofeng@gmail.com (Zhuofeng Luo)
import json
from datetime import datetime
from pathlib import Path
from enum import Enum

import click

from util import setup_logging, sync
from util_news import read_news_json, write_news_json
from util_summarize import init_openai, summarize_news_with_gpt
from util_tencent_news import get_tencent_hot_ranking_list
from util_tts import read_text_with_edge_tts, read_news_with_edge_tts, validate_edge_tts_voices
from util_video import generate_news_video, generate_news_video_description

_COVER_TXT = '十分钟带你看完时下热点。大家好，欢迎收听《十分热》每日新闻，今天是{year}年{month}月{day}日，星期{weekday}。'
_ENDING_TXT = '以上是全部内容，感谢您的收看，再见！'
_WEEKDAY_TO_CHINESE_CHAR = {
    0: '一',
    1: '二',
    2: '三',
    3: '四',
    4: '五',
    5: '六',
    6: '日',
}

_CONFIG = {}
with open('config.json', 'r') as f:
    _CONFIG = json.loads(f.read())


class NewsSource(Enum):
    TENCENT = 'tencent'


@click.group()
def main():
    setup_logging()


@main.command()
@click.option('--news_json', required=True, type=click.Path(dir_okay=False))
@click.option('--image_dir', required=True, type=click.Path(file_okay=False))
@click.option(
    '--source',
    type=click.Choice([news_source.value for news_source in NewsSource]),
    default='tencent')
@click.option('--news_num', default=20, type=int)
def fetch_news(news_json: str, image_dir: str, source: str, news_num: int):
    news_json_path = Path(news_json)
    news_json_path.parent.mkdir(parents=True, exist_ok=True)
    image_dir_path = Path(image_dir)
    image_dir_path.mkdir(parents=True, exist_ok=True)
    if source == NewsSource.TENCENT.value:
        news_list = get_tencent_hot_ranking_list(news_num=news_num, image_dir_path=image_dir_path)
    else:
        raise ValueError('Unknown news source {}'.format(source))
    write_news_json(news_list, news_json_path)


@main.command()
@click.option('--news_json', required=True, type=click.Path(dir_okay=False, exists=True))
def summarize_news(news_json: str):
    news_json_path = Path(news_json)
    news_list_without_summary = read_news_json(news_json_path)
    news_list = []
    init_openai(_CONFIG['openai_api_key'], _CONFIG['openai_proxy'])
    for news in news_list_without_summary:
        news_with_summary = summarize_news_with_gpt(news=news)
        if news_with_summary:
            news_list.append(news_with_summary)
    write_news_json(news_list, news_json_path)


@main.command()
@click.option('--news_json', required=True, type=click.Path(dir_okay=False, exists=True))
@click.option('--audio_dir', required=True, type=click.Path(file_okay=False))
@click.option('--voices', 'voices_str', default='zh-CN-YunyangNeural,zh-CN-YunjianNeural', type=str)
@click.option('--rate', default='+10%', type=str)
@click.option('--volume', default='+0%', type=str)
def read_news(news_json: str, audio_dir: str, voices_str: str, rate: str, volume: str):
    news_json_path = Path(news_json)
    news_list_without_audio = read_news_json(news_json_path)
    audio_dir_path = Path(audio_dir)
    audio_dir_path.mkdir(parents=True, exist_ok=True)
    news_list = []
    voices = voices_str.split(',')
    sync(validate_edge_tts_voices(voices))
    for index, news in enumerate(news_list_without_audio):
        audio_path = audio_dir_path / '{}.mp3'.format(str(index).zfill(2))
        news_with_audio = sync(
            read_news_with_edge_tts(
                news=news,
                audio_path=audio_path,
                voice=voices[index % len(voices)],
                rate=rate,
                volume=volume))
        if news_with_audio:
            news_list.append(news_with_audio)
    write_news_json(news_list, news_json_path)


@main.command()
@click.option('--cover_audio_file', required=True, type=click.Path(dir_okay=False))
@click.option('--ending_audio_file', required=True, type=click.Path(dir_okay=False))
@click.option('--date', default=datetime.now().strftime('%Y%m%d'), type=str)
@click.option('--voice', default='zh-CN-YunyangNeural', type=str)
@click.option('--rate', default='+10%', type=str)
@click.option('--volume', default='+0%', type=str)
def read_cover_and_ending(cover_audio_file: str, ending_audio_file: str, date: str, voice: str,
                          rate: str, volume: str):
    cover_audio_file_path = Path(cover_audio_file)
    ending_audio_file_path = Path(ending_audio_file)
    cover_audio_file_path.parent.mkdir(parents=True, exist_ok=True)
    ending_audio_file_path.parent.mkdir(parents=True, exist_ok=True)
    date_time = datetime(year=int(date[:4]), month=int(date[4:6]), day=int(date[6:8]))
    sync(validate_edge_tts_voices([voice]))
    sync(
        read_text_with_edge_tts(
            txt=_COVER_TXT.format(
                year=date_time.year,
                month=date_time.month,
                day=date_time.day,
                weekday=_WEEKDAY_TO_CHINESE_CHAR[date_time.weekday()]),
            audio_path=cover_audio_file_path,
            voice=voice,
            rate=rate,
            volume=volume))
    sync(
        read_text_with_edge_tts(
            txt=_ENDING_TXT,
            audio_path=ending_audio_file_path,
            voice=voice,
            rate=rate,
            volume=volume))


@main.command()
@click.option('--news_json', required=True, type=click.Path(dir_okay=False, exists=True))
@click.option('--cover_audio_file', required=True, type=click.Path(dir_okay=False, exists=True))
@click.option('--ending_audio_file', required=True, type=click.Path(dir_okay=False, exists=True))
@click.option('--date', default=datetime.now().strftime('%Y%m%d'), type=str)
@click.option('--video_file', required=True, type=click.Path(dir_okay=False))
@click.option('--cover_file', required=True, type=click.Path(dir_okay=False))
@click.option('--description_file', required=True, type=click.Path(dir_okay=False))
def record_news(news_json: str, cover_audio_file: str, ending_audio_file: str, date: str,
                video_file: str, cover_file: str, description_file: str):
    news_json_path = Path(news_json)
    cover_audio_file_path = Path(cover_audio_file)
    ending_audio_file_path = Path(ending_audio_file)
    news_list = read_news_json(news_json_path)
    video_file_path = Path(video_file)
    video_file_path.parent.mkdir(parents=True, exist_ok=True)
    cover_file_path = Path(cover_file)
    cover_file_path.parent.mkdir(parents=True, exist_ok=True)
    description_file_path = Path(description_file)
    description_file_path.parent.mkdir(parents=True, exist_ok=True)
    generate_news_video(
        news_list=news_list,
        date=date,
        cover_audio_file_path=cover_audio_file_path,
        ending_audio_file_path=ending_audio_file_path,
        font_file_path=Path(_CONFIG['video_font_path']),
        video_file_path=video_file_path,
        cover_file_path=cover_file_path)
    generate_news_video_description(
        news_list=news_list, date=date, description_file_path=description_file_path)


if __name__ == '__main__':
    main()
