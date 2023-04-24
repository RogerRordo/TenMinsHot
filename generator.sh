#!/bin/bash
set -e

readonly SCRIPT_DIR=$(readlink -f $(dirname ${BASH_SOURCE[0]}))
readonly DATA_DIR=${SCRIPT_DIR}/data
readonly DATE=$(date '+%Y%m%d')
readonly SUB_DATA_DIR=${DATA_DIR}/${DATE}

mkdir -p ${SUB_DATA_DIR}

echo "================================================== Start =================================================="

echo "================================================== Fetch News =================================================="
python3 src/news_generator.py fetch-news \
    --news_json ${SUB_DATA_DIR}/news.json

echo "================================================== Sumarize News =================================================="
python3 src/news_generator.py summarize-news \
    --news_json ${SUB_DATA_DIR}/news.json

echo "================================================== Read News =================================================="
python3 src/news_generator.py read-news \
    --news_json ${SUB_DATA_DIR}/news.json \
    --audio_dir ${SUB_DATA_DIR}/audios

echo "================================================== Read Cover \& Ending =================================================="
python3 src/news_generator.py read-cover-and-ending \
    --cover_audio_file ${SUB_DATA_DIR}/audios/cover.mp3 \
    --ending_audio_file ${SUB_DATA_DIR}/audios/ending.mp3 \
    --rate "-5%" \
    --date ${DATE}

echo "================================================== Record News =================================================="
python3 src/news_generator.py record-news \
    --news_json ${SUB_DATA_DIR}/news.json \
    --cover_audio_file ${SUB_DATA_DIR}/audios/cover.mp3 \
    --ending_audio_file ${SUB_DATA_DIR}/audios/ending.mp3 \
    --date ${DATE} \
    --video_file ${SUB_DATA_DIR}/video.mp4

echo "================================================== Finish =================================================="
