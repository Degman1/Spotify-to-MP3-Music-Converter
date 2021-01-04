# Spotify-to-MP3-Music-Converter
A text based application to download songs from a spotify playlist into MP3 format by downloading the song's lyrical youtube video. The songs are then organized in corresponding playlists in the output/ folder (the folder can be imported into apple music to sync with other local music for mac users).

Credit to the creator of https://github.com/brentvollebregt/spotify-playlist-downloader.git for inspiration for this project and the foundation for the downloading method.

# Usage
1. Run the SpotifyDownloader.ui file with python3
2. Use the help command for a guide to how to work the interface

TIP: Click the three dots at the top of a playlist (on the desktop version of Spotify), click share, and click "Copy Spotify URI" to retrieve the playlist's URI.

To update youtube_dl, run: sudo pip install -U youtube-dl (DISCLAIMER: youtube_dl was recently taken down by GitHub, so it may need to be downloaded from an indirect source)

-- If youtube_dl is out of date, the song downloading commands will likely fail.

# Developer Note: Convert SpotifyDownloaderUI.py to executable
1. Set the RunAsExec variable to True in the SpotifyDownloaderUI.py file
2. Open the terminal to the correct path and run: pyinstaller --onefile --add-data 'ffmpeg:.' --add-data 'ffprobe:.' --add-data 'ffplay:.' SpotifyDownloaderUI.py

