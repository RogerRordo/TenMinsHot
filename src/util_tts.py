# Copyright @2023. All rights reserved.
# Authors: luozhuofeng@gmail.com (Zhuofeng Luo)
import dataclasses
import logging
from pathlib import Path
from typing import List

from edge_tts import Communicate, list_voices

from class_news import News


async def validate_edge_tts_voices(voices: List[str]):
    supported_edge_tts_voices = {v['ShortName'] for v in await list_voices()}
    supported_edge_tts_voices = set(
        filter(lambda voice: voice.startswith('zh-'), supported_edge_tts_voices))
    unsupported_voices = [v for v in voices if v not in supported_edge_tts_voices]
    if unsupported_voices:
        raise ValueError('Unsupported voices: {}. All supported voices are: {}'.format(
            ', '.join(unsupported_voices), ', '.join(supported_edge_tts_voices)))


async def _read_with_edge_tts(txt: str, audio_path: Path, voice: str, rate: str, volume: str):
    tts = Communicate(
        text=txt,
        voice=voice,
        # proxy=proxy,
        rate=rate,
        volume=volume,
    )
    with open(str(audio_path), 'wb') as f:
        async for chunk in tts.stream():
            if chunk['type'] == 'audio':
                f.write(chunk['data'])


async def read_news_with_edge_tts(news: News, audio_path: Path, voice: str, rate: str,
                                  volume: str) -> News:
    await _read_with_edge_tts(
        txt='{}\n\n{}'.format(news.title, news.brief_content),
        audio_path=audio_path,
        voice=voice,
        rate=rate,
        volume=volume)
    news_with_audio = dataclasses.replace(news)
    news_with_audio.audio_path = str(audio_path)
    logging.info('Read content for {} to {}.'.format(news.title, str(audio_path)))
    return news_with_audio


async def read_text_with_edge_tts(txt: str, audio_path: Path, voice: str, rate: str, volume: str):
    await _read_with_edge_tts(txt=txt, audio_path=audio_path, voice=voice, rate=rate, volume=volume)
    logging.info('Read text to {}.'.format(str(audio_path)))
