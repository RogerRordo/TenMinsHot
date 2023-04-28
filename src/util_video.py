# Copyright @2023. All rights reserved.
# Authors: luozhuofeng@gmail.com (Zhuofeng Luo)
import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageFont, ImageDraw
from moviepy import editor

from class_news import News

# Global
_VIDEO_WIDTH = 1280
_VIDEO_HEIGHT = 720
_VIDEO_FPS = 50
_SPACING_LR = _VIDEO_WIDTH * 0.06
_SPACING_UB = _VIDEO_HEIGHT * 0.08
_SILENCE_BOUNDARY_SECS = 1
_FFMPEG_THREADS = 4
_BLACK_COLOR = 'black'
_WHITE_COLOR = (255, 255, 255)

# Cover
_COVER_TITLE_FONT_SIZE = 38
_COVER_TITLE_Y_OFFSET = -10
_COVER_DATE_FONT_SIZE = 18
_COVER_DATE_Y_OFFSET = 20
_COVER_DIVIDING_LINE_WIDTH = 5
_COVER_TOC_FONT_SIZE = 18
_COVER_TOC_X_OFFSET = 30
_COVER_TOC_Y_OFFSET = 10

# News
_CAPTION_FONT_SIZE = 28
_CAPTION_BBOX_HEIGHT = _VIDEO_HEIGHT * 0.07
_CAPTION_CONTENT_SPACING = _VIDEO_HEIGHT * 0.03
_CONTENT_FONT_SIZE = 25
_CONTENT_BBOX_HEIGHT = _VIDEO_HEIGHT * 0.66
_CONTENT_LINE_SPACING = 0.5
_CONTENT_SOURCE_SPACING = _VIDEO_HEIGHT * 0.03
_SOURCE_FONT_SIZE = 18
_NEWS_SLIDE_FILENAME_FMT = 'news_{}.png'


def with_temp_dir_path(func):

    def wrapper(*args, **kwargs):
        with tempfile.TemporaryDirectory() as temp_dir:
            return func(*args, **kwargs, temp_dir_path=Path(temp_dir))

    return wrapper


def _get_text_width_and_height(txt: str, font: ImageFont.FreeTypeFont):
    left, top, right, bottom = font.getbbox(txt)
    return right - left, bottom - top


def _add_text_box_with_word_wrap(draw: ImageDraw,
                                 bbox: Tuple[float, float, float, float],
                                 txt: str,
                                 font: ImageFont.FreeTypeFont,
                                 fill_color=_BLACK_COLOR,
                                 line_spacing: float = 0.25,
                                 align: str = 'left'):
    curr_x, curr_y, max_x, max_y = bbox[0], bbox[1], bbox[2], bbox[3]
    index = 0
    while index < len(txt):
        char_count = 1
        while all([
                curr_x + _get_text_width_and_height(txt[index:index + char_count], font)[0] < max_x,
                index + char_count < len(txt),
        ]):
            char_count += 1
        curr_line_txt = txt[index:index + char_count]
        _, curr_line_height = _get_text_width_and_height(curr_line_txt, font)
        if curr_y + curr_line_height > max_y:
            logging.warning('Textbox overflows by {} words'.format(len(txt) - index))
            return
        draw.text((curr_x, curr_y), curr_line_txt, font=font, align=align, fill=fill_color)
        index += char_count
        curr_y += curr_line_height * (1 + line_spacing)


def _generate_cover_slide(news_list: List[News], date: str, font_file_path: Path,
                          cover_slide_file_path: Path):
    canvas = Image.new('RGBA', (_VIDEO_WIDTH, _VIDEO_HEIGHT), _WHITE_COLOR)
    draw = ImageDraw.Draw(canvas)

    # Title
    title_txt = '《十分热》每日新闻'
    title_font = ImageFont.truetype(str(font_file_path), size=_COVER_TITLE_FONT_SIZE)
    _, _, title_width, title_height = draw.textbbox(
        (0, 0), title_txt, font=title_font, align='center')
    draw.text(
        ((_VIDEO_WIDTH / 3 - title_width) / 2,
         (_VIDEO_HEIGHT - title_height) / 2 + _COVER_TITLE_Y_OFFSET),
        title_txt,
        font=title_font,
        align='center',
        fill=_BLACK_COLOR)

    # Date
    date_txt = date
    date_font = ImageFont.truetype(str(font_file_path), size=_COVER_DATE_FONT_SIZE)
    _, _, date_width, date_height = draw.textbbox((0, 0), date_txt, font=date_font, align='center')
    draw.text(
        ((_VIDEO_WIDTH / 3 - date_width) / 2,
         (_VIDEO_HEIGHT - date_height) / 2 + title_height + _COVER_DATE_Y_OFFSET),
        date_txt,
        font=date_font,
        align='center',
        fill=_BLACK_COLOR)

    # Dividing line
    draw.line(
        (_VIDEO_WIDTH / 3, _SPACING_UB, _VIDEO_WIDTH / 3, _VIDEO_HEIGHT - _SPACING_UB),
        width=_COVER_DIVIDING_LINE_WIDTH,
        fill='#eee')

    # TOC
    toc_txt = '\n'.join([
        '【{}/{}】{}'.format(str(index + 1).zfill(2),
                           str(len(news_list)).zfill(2), news.title)
        for index, news in enumerate(news_list)
    ])
    toc_font = ImageFont.truetype(str(font_file_path), size=_COVER_TOC_FONT_SIZE)
    draw.text(
        (_VIDEO_WIDTH / 3 + _COVER_TOC_X_OFFSET, _SPACING_UB + _COVER_TOC_Y_OFFSET),
        toc_txt,
        font=toc_font,
        align='left',
        fill=_BLACK_COLOR)

    canvas.save(str(cover_slide_file_path))
    logging.info('Exported temp cover slide to {}'.format(str(cover_slide_file_path)))


def _generate_news_slide(news: News, news_index: int, news_length: int, font_file_path: Path,
                         news_slide_file_path: Path):
    # TODO: Support background image
    canvas = Image.new('RGBA', (_VIDEO_WIDTH, _VIDEO_HEIGHT), _WHITE_COLOR)
    draw = ImageDraw.Draw(canvas)
    has_image = False
    if news.image_path:
        try:
            news_image = Image.open(news.image_path)
        except Exception as exception:  # pylint: disable=broad-except
            logging.exception('Failed to open image for the news {}, ignore it. {}'.format(
                news.title, exception))
        else:
            has_image = True

    # Caption
    caption_txt = '【{}/{}】{}'.format(
        str(news_index + 1).zfill(2),
        str(news_length).zfill(2), news.title)
    caption_font = ImageFont.truetype(str(font_file_path), size=_CAPTION_FONT_SIZE)
    _add_text_box_with_word_wrap(
        draw=draw,
        bbox=(_SPACING_LR, _SPACING_UB, _VIDEO_WIDTH - _SPACING_LR,
              _SPACING_UB + _CAPTION_BBOX_HEIGHT),
        txt=caption_txt,
        font=caption_font)

    # Content
    content_txt = news.brief_content
    content_font = ImageFont.truetype(str(font_file_path), size=_CONTENT_FONT_SIZE)
    if has_image:
        content_bbox = (
            _SPACING_LR,
            _SPACING_UB + _CAPTION_BBOX_HEIGHT + _CAPTION_CONTENT_SPACING,
            _VIDEO_WIDTH / 2 - _SPACING_LR,
            _SPACING_UB + _CAPTION_BBOX_HEIGHT + _CAPTION_CONTENT_SPACING + _CONTENT_BBOX_HEIGHT,
        )
    else:
        content_bbox = (
            _SPACING_LR,
            _SPACING_UB + _CAPTION_BBOX_HEIGHT + _CAPTION_CONTENT_SPACING,
            _VIDEO_WIDTH - _SPACING_LR,
            _SPACING_UB + _CAPTION_BBOX_HEIGHT + _CAPTION_CONTENT_SPACING + _CONTENT_BBOX_HEIGHT,
        )
    _add_text_box_with_word_wrap(
        draw=draw,
        bbox=content_bbox,
        txt=content_txt,
        font=content_font,
        line_spacing=_CONTENT_LINE_SPACING)

    # Image
    if has_image:
        image_ratio = news_image.size[0] / news_image.size[1]
        image_width = _VIDEO_WIDTH / 2 - _SPACING_LR * 2
        image_height = int(min(image_width / image_ratio, _CONTENT_BBOX_HEIGHT))
        image_width = int(image_ratio * image_height)
        news_image = news_image.resize((image_width, image_height))
        image_center = (_VIDEO_WIDTH * 3 / 4, _SPACING_UB + _CAPTION_BBOX_HEIGHT +
                        _CAPTION_CONTENT_SPACING + _CONTENT_BBOX_HEIGHT / 2)
        canvas.paste(
            news_image,
            (int(image_center[0] - image_width / 2), int(image_center[1] - image_height / 2)))

    # Source
    content_txt = f'来源：{news.source_name} {news.url}'
    content_font = ImageFont.truetype(str(font_file_path), size=_SOURCE_FONT_SIZE)
    _add_text_box_with_word_wrap(
        draw=draw,
        bbox=(_SPACING_LR, _SPACING_UB + _CAPTION_BBOX_HEIGHT + _CAPTION_CONTENT_SPACING +
              _CONTENT_BBOX_HEIGHT + _CONTENT_SOURCE_SPACING, _VIDEO_WIDTH - _SPACING_LR,
              _VIDEO_HEIGHT - _SPACING_UB),
        txt=content_txt,
        font=content_font)

    canvas.save(str(news_slide_file_path))
    logging.info('Exported temp news slide for {} to {}'.format(news.title,
                                                                str(news_slide_file_path)))


@with_temp_dir_path
def generate_news_video(news_list: List[News],
                        date: str,
                        cover_audio_file_path: Path,
                        ending_audio_file_path: Path,
                        font_file_path: Path,
                        video_file_path: Path,
                        cover_file_path: Path,
                        temp_dir_path: Optional[Path] = None):
    if temp_dir_path is None:
        raise ValueError('Temp dir path cannot be none')
    bg_white_clip = editor.ColorClip(size=(_VIDEO_WIDTH, _VIDEO_HEIGHT), color=_WHITE_COLOR)
    curr_timestamp = 0

    # Generate slides
    _generate_cover_slide(
        news_list=news_list,
        date=date,
        font_file_path=font_file_path,
        cover_slide_file_path=cover_file_path)
    for index, news in enumerate(news_list):
        _generate_news_slide(
            news=news,
            news_index=index,
            news_length=len(news_list),
            font_file_path=font_file_path,
            news_slide_file_path=temp_dir_path / _NEWS_SLIDE_FILENAME_FMT.format(
                str(index).zfill(2)))

    # Cover
    cover_slide_clip = editor.ImageClip(str(cover_file_path))
    cover_audio_clip = editor.AudioFileClip(str(cover_audio_file_path))
    cover_slide_clip = cover_slide_clip.set_position((0, 0))
    cover_slide_clip = cover_slide_clip.set_start((curr_timestamp))
    cover_slide_clip = cover_slide_clip.set_duration(
        cover_audio_clip.duration + _SILENCE_BOUNDARY_SECS * 2)
    curr_timestamp += _SILENCE_BOUNDARY_SECS
    cover_audio_clip = cover_audio_clip.set_start((curr_timestamp))
    curr_timestamp += cover_audio_clip.duration + _SILENCE_BOUNDARY_SECS

    # News content
    news_slide_clips = []
    news_audio_clips = []
    for index, news in enumerate(news_list):
        # Init clips
        news_slide_clip = editor.ImageClip(
            str(temp_dir_path / _NEWS_SLIDE_FILENAME_FMT.format(str(index).zfill(2))))
        news_audio_clip = editor.AudioFileClip(str(news.audio_path))

        # Set clips' attrs
        news_slide_clip = news_slide_clip.set_position((0, 0))
        news_slide_clip = news_slide_clip.set_start((curr_timestamp))
        news_slide_clip = news_slide_clip.set_duration(
            news_audio_clip.duration + _SILENCE_BOUNDARY_SECS * 2)

        curr_timestamp += _SILENCE_BOUNDARY_SECS
        news_audio_clip = news_audio_clip.set_start((curr_timestamp))
        curr_timestamp += news_audio_clip.duration + _SILENCE_BOUNDARY_SECS

        # Add to lists
        news_slide_clips.append(news_slide_clip)
        news_audio_clips.append(news_audio_clip)

    # Ending
    ending_slide_clip = editor.ImageClip(str(cover_file_path))
    ending_audio_clip = editor.AudioFileClip(str(ending_audio_file_path))
    ending_slide_clip = ending_slide_clip.set_position((0, 0))
    ending_slide_clip = ending_slide_clip.set_start((curr_timestamp))
    ending_slide_clip = ending_slide_clip.set_duration(
        ending_audio_clip.duration + _SILENCE_BOUNDARY_SECS * 2)
    curr_timestamp += _SILENCE_BOUNDARY_SECS
    ending_audio_clip = ending_audio_clip.set_start((curr_timestamp))
    curr_timestamp += ending_audio_clip.duration + _SILENCE_BOUNDARY_SECS

    # Combine all clips
    bg_white_clip = bg_white_clip.set_duration(curr_timestamp)
    final_video_clip = editor.CompositeVideoClip(
        [bg_white_clip, cover_slide_clip, *news_slide_clips, ending_slide_clip])
    final_audio_clip = editor.CompositeAudioClip(
        [cover_audio_clip, *news_audio_clips, ending_audio_clip])
    final_video_clip = final_video_clip.set_audio(final_audio_clip)

    final_video_clip.write_videofile(str(video_file_path), fps=_VIDEO_FPS, threads=_FFMPEG_THREADS)
    logging.info('Generated news video to {}'.format(str(video_file_path)))


def generate_news_video_description(news_list: List[News], date: str, description_file_path: Path):
    descriptions = [
        '《十分热》每日新闻 - {}期'.format(date),
        '爬虫 + ChatGPT + TTS 全自动生成的新闻视频，十分钟带你看完24h时下热点。',
        'https://github.com/RogerRordo/TenMinsHot',
        '',
    ] + [
        '{}. 《{}》'.format(str(index).zfill(2), news.title) for index, news in enumerate(news_list)
    ]
    description = '\n'.join(descriptions)
    description_file_path.write_text(description)
    logging.info('Generated description text for the video to {}'.format(
        str(description_file_path)))
