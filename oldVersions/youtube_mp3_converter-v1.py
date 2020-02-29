#!/usr/bin/env python3

import youtube_dl

ui = ""
urls = []
while ui != "q":
    ui = input("enter url...")
    if ui != "q" and ui != "":  #Just in case I make a mistake typing it in
        urls.append(ui)

ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',}],
    }

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download(urls)