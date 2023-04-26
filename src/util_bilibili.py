# Copyright @2023. All rights reserved.
# Authors: luozhuofeng@gmail.com (Zhuofeng Luo)
import logging
from pathlib import Path
from typing import List

from bilibili_api import sync, homepage, video_uploader, Credential


class UtilBilibili():

    is_initialized = False

    @classmethod
    def init(cls, sessdata: str, bili_jct: str, buvid3):
        cls.credential = Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)
        cls.is_initialized = True

    @classmethod
    def check_login(cls) -> bool:
        if not cls.is_initialized:
            return False
        try:
            sync(homepage.get_videos())
        except:  # pylint: disable=bare-except
            return False
        else:
            return True

    @classmethod
    async def _upload(cls, video_file_path: Path, cover_file_path: Path, title: str,
                      description: str, metadata: dict):
        page = video_uploader.VideoUploaderPage(
            path=str(video_file_path), title=title, description=description)
        uploader = video_uploader.VideoUploader(
            [page], metadata, cls.credential, cover=str(cover_file_path))

        @uploader.on('__ALL__')
        async def ev(data):  # pylint: disable=unused-variable
            logging.info(data)

        await uploader.start()

    @classmethod
    def upload(cls,
               video_file_path: Path,
               cover_file_path: Path,
               title: str,
               description: str,
               tags: List[str],
               tid: int = 124):
        # ref: https://nemo2011.github.io/bilibili-api/#/modules/video_uploader
        metadata = {
            'act_reserve_create': 0,
            'copyright': 1,
            'source': '',
            'desc': description,
            'desc_format_id': 0,
            'dynamic': '',
            'interactive': 0,
            'no_reprint': 1,
            'open_elec': 0,
            'origin_state': 0,
            'subtitles': {
                'lan': '',
                'open': 0,
            },
            'tag': ','.join(tags),
            'tid': tid,
            'title': title,
            'up_close_danmaku': False,
            'up_close_reply': False,
            'up_selection_reply': False,
            'dtime': 0,
        }
        try:
            sync(cls._upload(video_file_path, cover_file_path, title, description, metadata))
        except Exception as e:  # pylint: disable=broad-except
            logging.exception('Failed to upload {} to bilibili: {}'.format(str(video_file_path), e))
