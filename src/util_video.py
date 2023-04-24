# Copyright @2023. All rights reserved.
# Authors: luozhuofeng@gmail.com (Zhuofeng Luo)
import logging
import textwrap
from pathlib import Path
from typing import List

from moviepy import editor

from class_news import News

_VIDEO_WIDTH = 1280
_VIDEO_HEIGHT = 720
_VIDEO_FPS = 50
_FONT = 'Noto-Sans-CJK-HK-Bold'
_COVER_TITLE_FONT_SIZE = 50
_SPACING_LR = int(_VIDEO_WIDTH * 0.08)
_SPACING_UB = int(_VIDEO_HEIGHT * 0.08)
_CAPTION_AND_CONTENT_WIDTH = _VIDEO_WIDTH - _SPACING_LR * 2
_CAPTION_FONT_SIZE = 26
_CAPTION_CONTENT_SPACING = int(_VIDEO_HEIGHT * 0.04)
_CONTENT_FONT_SIZE = 23
_CONTENT_WRAP_WIDTH = 40
_SILENCE_BOUNDARY_SECS = 1
_FFMPEG_THREADS = 4


def generate_news_video(news_list: List[News], date: str, cover_audio_file_path: Path,
                        ending_audio_file_path: Path, video_file_path: Path):
    bg_white_clip = editor.ColorClip(size=(_VIDEO_WIDTH, _VIDEO_HEIGHT), color=(255, 255, 255))
    curr_timestamp = 0

    # Cover
    cover_txt_clip = editor.TextClip(
        txt='十分热\n{}'.format(date),
        font=_FONT,
        fontsize=_COVER_TITLE_FONT_SIZE,
        method='caption',
        align='Center',
        print_cmd=True)
    cover_audio_clip = editor.AudioFileClip(str(cover_audio_file_path))
    cover_txt_clip = cover_txt_clip.set_position(('center', 'center'))
    cover_txt_clip = cover_txt_clip.set_start((curr_timestamp))
    cover_txt_clip = cover_txt_clip.set_duration(
        cover_audio_clip.duration + _SILENCE_BOUNDARY_SECS * 2)
    curr_timestamp += _SILENCE_BOUNDARY_SECS
    cover_audio_clip = cover_audio_clip.set_start((curr_timestamp))
    curr_timestamp += cover_audio_clip.duration + _SILENCE_BOUNDARY_SECS

    # Content
    caption_clips = []
    brief_content_clips = []
    audio_clips = []
    for index, news in enumerate(news_list):
        # Complete brief content
        wrapped_brief_content = '\n'.join(textwrap.wrap(news.brief_content, _CONTENT_WRAP_WIDTH))
        final_brief_content = '{}\n\nSource: {}'.format(wrapped_brief_content, news.url)

        # Init clips
        caption_clip = editor.TextClip(
            txt='[{}/{}]{}'.format(index + 1, len(news_list), news.title),
            font=_FONT,
            fontsize=_CAPTION_FONT_SIZE,
            size=(_CAPTION_AND_CONTENT_WIDTH, None),
            method='caption',
            align='NorthWest',
            print_cmd=True)
        brief_content_clip = editor.TextClip(
            txt=final_brief_content,
            font=_FONT,
            fontsize=_CONTENT_FONT_SIZE,
            size=(_CAPTION_AND_CONTENT_WIDTH, None),
            method='caption',
            align='NorthWest',
            print_cmd=True)
        audio_clip = editor.AudioFileClip(str(news.audio_path))

        # Set clips' attrs
        caption_clip = caption_clip.set_position((_SPACING_LR, _SPACING_UB))
        caption_clip = caption_clip.set_start((curr_timestamp))
        caption_clip = caption_clip.set_duration(audio_clip.duration + _SILENCE_BOUNDARY_SECS * 2)
        brief_content_clip = brief_content_clip.set_position(
            (_SPACING_LR, _SPACING_UB + caption_clip.size[1] + _CAPTION_CONTENT_SPACING))
        brief_content_clip = brief_content_clip.set_start((curr_timestamp))
        brief_content_clip = brief_content_clip.set_duration(
            audio_clip.duration + _SILENCE_BOUNDARY_SECS * 2)

        curr_timestamp += _SILENCE_BOUNDARY_SECS
        audio_clip = audio_clip.set_start((curr_timestamp))
        curr_timestamp += audio_clip.duration + _SILENCE_BOUNDARY_SECS

        # Add to lists
        caption_clips.append(caption_clip)
        brief_content_clips.append(brief_content_clip)
        audio_clips.append(audio_clip)

    # Ending
    ending_txt_clip = editor.TextClip(
        txt='十分热\n{}'.format(date),
        font=_FONT,
        fontsize=_COVER_TITLE_FONT_SIZE,
        method='caption',
        align='Center',
        print_cmd=True)
    ending_audio_clip = editor.AudioFileClip(str(ending_audio_file_path))
    ending_txt_clip = ending_txt_clip.set_position(('center', 'center'))
    ending_txt_clip = ending_txt_clip.set_start((curr_timestamp))
    ending_txt_clip = ending_txt_clip.set_duration(
        ending_audio_clip.duration + _SILENCE_BOUNDARY_SECS * 2)
    curr_timestamp += _SILENCE_BOUNDARY_SECS
    ending_audio_clip = ending_audio_clip.set_start((curr_timestamp))
    curr_timestamp += ending_audio_clip.duration + _SILENCE_BOUNDARY_SECS

    # Combine all clips
    bg_white_clip = bg_white_clip.set_duration(curr_timestamp)
    final_video_clip = editor.CompositeVideoClip(
        [bg_white_clip, cover_txt_clip, *caption_clips, *brief_content_clips, ending_txt_clip])
    final_audio_clip = editor.CompositeAudioClip(
        [cover_audio_clip, *audio_clips, ending_audio_clip])
    final_video_clip = final_video_clip.set_audio(final_audio_clip)

    final_video_clip.write_videofile(str(video_file_path), fps=_VIDEO_FPS, threads=_FFMPEG_THREADS)
    logging.info('Generated news video to {}'.format(str(video_file_path)))
