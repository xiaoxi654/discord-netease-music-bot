import os
import shutil
import stat
import requests
from mutagen.mp3 import MP3


def get_music_info(music_id: str):
    searchResult = requests.get('https://api.imjad.cn/cloudmusic/?type=search&search_type=1&s=' + music_id).json()
    musicId = str(searchResult['result']['songs'][0]['id'])
    musicResult = requests.get('https://api.imjad.cn/cloudmusic/?type=music&br=320000&id=' + musicId).json()
    musicUrl = musicResult['data'][0]['url']
    musicTitle = searchResult['result']['songs'][0]['name']
    musicPic = searchResult['result']['songs'][0]['al']['picUrl']
    musicArResult = '/'.join([m["name"] for m in searchResult["result"]["songs"][0]["ar"]])
    musicFileName = download_music(musicId, musicUrl)
    musicLengthSecond = int(round(MP3(musicFileName).info.length))
    lengthMinute, lengthSecond = divmod(musicLengthSecond, 60)
    music_info = {
        "163Url": "https://music.163.com/#/song?id=" + musicId,
        "musicId": musicId,
        "musicUrl": musicUrl,
        "musicTitle": musicTitle,
        "musicArResult": musicArResult,
        "musicPic": musicPic,
        "musicFileName": musicFileName,
        "musicLength": ("%02d:%02d" % (lengthMinute, lengthSecond))
        }
    return music_info


def download_music(music_id: str, music_url: str):
    fileName = 'tmp/' + music_id + '.mp3'
    if os.path.exists("tmp/") is not True:  # 如果 tmp 文件夹未被创建，则创建 tmp 文件夹
        os.mkdir("tmp/")
    with open(fileName, 'wb') as music:
        music.write(requests.get(music_url).content)
    return str(fileName)


def clean_cache():
    if os.path.exists('tmp'):
        for fileList in os.walk('tmp'):
            for name in fileList[2]:
                os.chmod(os.path.join(fileList[0], name), stat.S_IWRITE)
                os.remove(os.path.join(fileList[0], name))
            shutil.rmtree('tmp')


class Queue:
    def __init__(self):
        self.music_list = []

    def is_empty(self):
        return self.music_list == []

    def enqueue(self, music_info):
        self.music_list.insert(0, music_info)

    def dequeue(self):
        return self.music_list.pop()

    def size(self):
        return len(self.music_list)

    def clear(self):
        self.music_list.clear()
