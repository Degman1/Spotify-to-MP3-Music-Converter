# Spotify-to-MP3-Music-Converter
*** Complies with all YouTube copyright requirements, for personal use only ***

A text based application to download songs from a spotify playlist into MP3 format by downloading the song's lyrical youtube video. The songs are then organized in corresponding playlists in the output/ folder (the folder can be imported into apple music to sync with other local music for mac users).

Credit to the GitHub user brentvollebregt for inspiration for this project.

# Usage

## Executable File

1. Open the executable file named SpotifyDownloaderUI (will take a second to load the terminal session)
2. The output folder for downloaded playlists will be created adjacent to the location of the executable file

## Python File

1. Install all packages specified in the requirements.txt file
2. Run the SpotifyDownloaderUI.py file with python3 (I wrote the program using Python 3.8.1)
3. The output folder for downloaded playlists will be created adjacent to the location of the Python file

# Tips

Click the three dots at the top of a playlist (on the desktop version of Spotify), click share, and click "Copy Spotify URI" to retrieve the playlist's URI.

Make sure your version of youtube_dl is up to date, as if it is not, the downloading commands will likely be unsuccessful. To update youtube_dl after it is already installed with pip, run: sudo pip install -U youtube-dl
