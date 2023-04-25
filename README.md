# TenMinsHot
《十分热》是每日自动生成的十分钟左右的时事快讯视频节目。原理是爬取腾讯新闻，用ChatGpt总结，并用微软TTS朗读。

## Usage

1. 需要在Linux下安装python3.8以上，并通过pip安装`requirements.txt`内的包
2. 安装`sudo apt-get install imagemagick`
3. 复制 `example.config.json` 为 `config.json`，并填入openai的api key和proxy（如果需要，否则为空）
4. 在本目录下运行`./generator.sh`
5. 如无意外，`./data/{YYYYMMDD}/video.mp4`将生成新闻视频
