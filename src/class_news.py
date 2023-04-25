# Copyright @2023. All rights reserved.
# Authors: luozhuofeng@gmail.com (Zhuofeng Luo)

from dataclasses import asdict, dataclass


@dataclass
class News():
    title: str
    content: str
    url: str
    publish_timestamp: float
    request_timestamp: float
    source_name: str = ''
    comment_count: int = 0
    image_path: str = ''
    brief_content: str = ''
    audio_path: str = ''

    def as_dict(self) -> dict:
        return asdict(self)
