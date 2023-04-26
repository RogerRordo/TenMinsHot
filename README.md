# TenMinsHot
《十分热》是每日自动生成的十分钟左右的时事快讯视频节目。原理是爬取腾讯新闻，用ChatGpt总结，并用微软TTS朗读。

https://space.bilibili.com/695795/video

## Usage

1. 安装 python 3.9 和 [pipenv](https://pythonguidecn.readthedocs.io/zh/latest/dev/virtualenvs.html)
2. 在本目录下运行 `pipenv install` 以安装依赖
3. 复制 `example.config.json` 为 `config.json`，并填入 openai 的 api key 和代理 proxy（如果需要，否则为空）
4. 在本目录下运行 `./generator.sh`
5. 如无意外，将生成当日新闻视频在 `./data/{YYYYMMDD}/video.mp4`

若在 `config.json` 中按[bilibili-api的doc](https://nemo2011.github.io/bilibili-api/#/get-credential)配上B站cookies，可将第四步改为 `./generator.sh --upload` 直接在生成视频后自动上传B站。如果要上传已经生成好的视频，请用

```
pipenv run python3 src/video_uploader.py upload-to-bilibili \
    --date {date} \
    --video_file {video_file} \
    --cover_file {cover_file} \
    --description_file {description_file}
```
