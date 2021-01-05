"""
SpotifyDownloaderClient to handle the downloading of songs retrieving data from spotify, downloading the 
songs off of youtube, and converting them into mp3 files. Credit for the downloading methods along with various 
peices of the code goes to the creator of spotify_album_downloader.py on github

"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time

import ffmpeg
import ffprobe

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error, TYER
from mutagen.easyid3 import EasyID3
import youtube_dl
import urllib.request
import ssl
from bs4 import BeautifulSoup
import os
import sys
import requests

from Settings import Settings

class SpotifyDownloaderClient:
    sp = None   #holds spotify client credentials
    rcp = {}    #Stores recently changed playlists
    gcontext = ssl.SSLContext()

    def __init__(self, cwd):
        self.cwd = cwd
        client_id = "5b3b65211f7c41f4b82084314968be82"
        client_secret = "c39e11f27e974db690a8440fa4cc47b5"
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        #self.sp.trace = False
    
    @staticmethod
    def announceCompletion(str):
        print("*** " + str)
    
    @staticmethod
    def printErrorMessage(message, e = None, includeERRORWord = True):     # e is the actual program error message
        errorWord = "ERROR: "
        if not includeERRORWord:
            errorWord = "   "

        redColor = '\x1b[0;31m'
        blackColor = '\x1B[0m'

        # start with color you want, end with color for future prints (ie. go back to normal black)
        print(redColor, end="")
        
        if Settings.DEBUG_MODE and e != None:
            errorType = type(e).__name__
            fileLocation = __file__
            lineNumber = e.__traceback__.tb_lineno
            print(errorWord + message + " :: ")
            print("   message = \"" + str(e) + "\", errorType = \"" + str(errorType) + "\", fileLocation = \"" + str(fileLocation) + "\", lineNumber = \"" + str(lineNumber))
        else:
            print(errorWord + message)
        
        print(blackColor, end="")
    
    @staticmethod
    def stripString(text):
        return "".join([i for i in text if i not in [i for i in '/\\:*?"><|']])
    
    @staticmethod
    def my_hook(d):
        if '_percent_str' in d:
            if d['status'] == 'downloading':
                print ("\r" + d['_percent_str'], end = "")
        #if d['status'] == 'finished':
        #    print ('\rDone downloading, now converting ...')
    
    def getContents(self, playlist_name):
        if os.path.exists(self.cwd + "/output/" + playlist_name):
            c = os.listdir(self.cwd + "/output/" + playlist_name)
            if ".DS_Store" in c:
                c.remove(".DS_Store")
            if ".uri.txt" in c:
                c.remove(".uri.txt")
            return c
        else:
            return None
    
    class MyLogger(object):
        def debug(self, msg):
            pass

        def warning(self, msg):
            if Settings.DEBUG_MODE:
                print(str(msg))

        def error(self, msg):
            if Settings.DEBUG_MODE:
                print(str(msg))

    def downloadYoutubeToMP3(self, link, outputPath):
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'logger': self.MyLogger(),
            'progress_hooks': [SpotifyDownloaderClient.my_hook],
            'nocheckcertificate': True,
            'outtmpl': outputPath
        }

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                a = ydl.download([link])    #TODO: try fetching all the links first and then download all the songs afterwards, might be faster?
            return True
        except Exception:
            return False
    
    def directorySetup(self, playlist_name):
        if not os.path.exists(self.cwd + "/output/"):                          #make sure the output dir is there
            os.makedirs(self.cwd + "/output/")
        if not os.path.exists(self.cwd + "/output/" + playlist_name + "/"):    #make new dir for individual playlist
            os.makedirs(self.cwd + "/output/" + playlist_name)
        
        SpotifyDownloaderClient.announceCompletion("Directory Setup Successful")

    def filterOutPreDownloadedSongs(self, individual_songs, contents):
        contents = "\n".join(contents).lower()
        individual_songs_temp = []
        # Be careful not to mistake songs with the same 'name' as being the same. They could have the same 
        # general name provided by spotify but still actually be a different song

        for song in individual_songs:
            title = SpotifyDownloaderClient.stripString(song['track']['name']).lower()
            if title not in contents:
                individual_songs_temp.append(song)
            #else:
            #    print("The song %s is already downloaded into this playlist" % (title))
        
        SpotifyDownloaderClient.announceCompletion("Song Filtering Successful")
        return individual_songs_temp

    def retrieveSongData(self, uri, playlist_name):
        individual_songs = []
        song_data = {}
        
        split = uri.split(":")
        if uri.count(":") != 2 or split[1] != "playlist":
            SpotifyDownloaderClient.printErrorMessage("Invalid URI")
            return None
        playlist_id = split[2]
        offset = 0
        results = self.sp.user_playlist_tracks("RandoUser", playlist_id, offset=offset, fields="next,items") #For some reason the user does not matter even though the method requires it...
        individual_songs += results['items']

        while (results['next'] != None):
            offset += 100
            results = self.sp.user_playlist_tracks("RandoUser", playlist_id, offset=offset)
            individual_songs += results['items']
        
        contents = self.getContents(playlist_name)
        if contents is None:
            return None
        individual_songs = self.filterOutPreDownloadedSongs(individual_songs, contents)

        for song in individual_songs:
            track = song['track']
            song_data[track['uri']] = {'artist' : track['artists'][0]['name'],
                                    'album' : track['album']['name'],
                                    'title' : track['name'],
                                    'ablum_art' : track['album']['images'][0]['url'],
                                    'track' : str(track['track_number']),
                                    'name' : song['track']['name'],
                                    'id' : song['track']['id']}
        
        SpotifyDownloaderClient.announceCompletion("Song Data Retrieval Successful")
        return song_data

    def getVideoURL(self, song_data, song):
        search_term = song_data[song]['artist'] + " " + song_data[song]['title'] + " lyrics"
        Search_URL = ''.join([i for i in filter(lambda x: x in set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r\x0b\x0c'), "https://www.youtube.com/results?search_query=" + '+'.join(search_term.replace("&", "%26").replace("=", "%3D").replace("*", "%3D").split(" ")))])
        
        html = requests.get(Search_URL).text
        key = "\"webCommandMetadata\":{\"url\":\"/watch?v="
        index = html.find(key)

        if index == -1:
            return None

        index += len(key)
        link = ""

        while html[index] != "\"":
            link += str(html[index])
            index += 1

        r = "https://www.youtube.com" + "/watch?v=" + link
        return r

    def downloadSongOriginYoutube(self, video_URL, song_name, playlist_name):
        self.directorySetup(playlist_name)

        files_in_cd = os.listdir(os.getcwd())
        for i in files_in_cd:
            if i.endswith(".mp3"):
                os.remove(self.cwd + "/" + i)
    
        a = self.downloadYoutubeToMP3(video_URL, "/temporaryName.mp3")
        if not a:
            SpotifyDownloaderClient.printErrorMessage("Could not download requested song. Please try a different URL (different youtube video)")
            return
        
        print("\rDownload and conversion complete")

        file = None
        files_in_cd = os.listdir(os.getcwd())
        for i in files_in_cd:
            if i.endswith(".mp3"):
                file = os.getcwd() + "/" + i

        audio = MP3(file, ID3=ID3)
        
        try:
            audio.add_tags()
        except error:
            pass

        audio = EasyID3(file)
        audio["title"] = song_name
        audio.save()

        name = self.cwd + "/output/" + str(playlist_name) + "/" + (song_name) + ".mp3"  #TODO fix this stuff
        
        os.rename(file, name)
        print("Saved at: " + name)
        print()

    def downloadSongOriginSpotify(self, song_data, song, playlist_name):
        try:
            link = self.getVideoURL(song_data, song)
            
            if link == None:
                SpotifyDownloaderClient.printErrorMessage("Failed to find a Youtube link for this song")
                return 0
            
            print("Video Link = " + link)
            
            title_stripped = SpotifyDownloaderClient.stripString(song_data[song]['title'])
            downloadedFilePath = title_stripped + ".mp3"

            for i in range(20):
                if os.path.exists(downloadedFilePath):
                    downloadedFilePath = title_stripped + " (" + str(i) + ")" + ".mp3"

            if os.path.exists(downloadedFilePath):
                SpotifyDownloaderClient.printErrorMessage("After 20 attempts to rename the downloaded mp3 file, every attempted file name already existed in the current playlist folder. Either remove one of those songs from the playlist or contact the program developer")
                return 0

            success = False

            for i in range(5):
                success = self.downloadYoutubeToMP3(link, downloadedFilePath)
                if not success:
                    SpotifyDownloaderClient.printErrorMessage("Video download attempt " + str(i + 1) + "/5 failed")

            if not success:
                return 0

            print ("\rDownload and conversion complete")
            
            if not os.path.exists(downloadedFilePath):
                SpotifyDownloaderClient.printErrorMessage("The downloaded mp3 file could not be located, please locate it yourself in the playlist folder named \"" + playlist_name + "\"")
                return
   
            try:
                audio = MP3(downloadedFilePath, ID3=ID3)
            except Exception as e:
                SpotifyDownloaderClient.printErrorMessage("The file downloaded from youtube was likely corrupted, please attempt to download again", e)
                return 0
            
            try:
                audio.add_tags()
            except error:
                pass
            
            # add album art to the mp3 file
            urllib.request.urlretrieve(song_data[song]['ablum_art'], (self.cwd + "/TempAArtImage.jpg"))
            audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc=u'cover', data=open(self.cwd + "/" + playlist_name + "/TempAArtImage.jpg", 'rb').read()))
            audio.save()
            os.remove(self.cwd + "/" + playlist_name + "/TempAArtImage.jpg")

            # now add the remaining information provided by Spotify to the mp3 file
            # the object stored under audio is changed to type EasyID3 in order to do so
            audio = EasyID3(downloadedFilePath)
            audio["tracknumber"] = song_data[song]['track']
            audio["title"] = song_data[song]['title']
            audio["album"] = song_data[song]['album']
            audio["artist"] = song_data[song]['artist']
            audio["genre"] = playlist_name #this allows the user to add the song to the apple music library and create a smart-playlist to only include songs from a certain genre
            audio.save()

        except Exception as e:
            SpotifyDownloaderClient.printErrorMessage("Fatal - Please contact the program designer for help", e)
            return 0
    
    def downloadSpotifyPlaylist(self, song_data, playlist_name):
        total = len(song_data)
        complete_counter = 0
        success_counter = 0

        for song in song_data:
            title = song_data[song]['title']
            artist = song_data[song]['artist']

            complete_counter += 1

            print("\nStarting song %s/%s: %s by %s" % (complete_counter, total, title, artist))

            result = self.downloadSongOriginSpotify(song_data, song, playlist_name)

            if result == 1:      # successful, continue program
                success_counter += 1

                #update the recently changed playlists dictionary
                if playlist_name not in self.rcp.keys():
                    self.rcp[playlist_name] = {title}
                else:
                    self.rcp[playlist_name].add(title)
            elif result == 0:    # failed, continue program
                SpotifyDownloaderClient.printErrorMessage("Unable to download the song %s by %s" % (title, artist), includeERRORWord = False)
            elif result == -1:   # fialed, stop program
                return

        all_songs = os.listdir(self.cwd + "/output/" + playlist_name + "/")
        n_all_songs = len(all_songs)

        if ".uri.txt" in all_songs:
            n_all_songs -= 1
        if ".DS_Store" in all_songs:
            n_all_songs -= 1
        
        if total == 0:
            SpotifyDownloaderClient.announceCompletion("Playlist %s is already up to date" % playlist_name)
        else:
            SpotifyDownloaderClient.announceCompletion("Successful Downloads: %s/%s" % (success_counter, total))
        
        SpotifyDownloaderClient.announceCompletion("There are now %s songs in the playlist %s" % (n_all_songs, playlist_name))
        print()

    def runDownload(self, uri, playlist_name):
        self.directorySetup(playlist_name)                      # setup correct directories required for download
        song_data = self.retrieveSongData(uri, playlist_name)   # retrieve song data from spotify playlist
        if song_data is not None:
            self.downloadSpotifyPlaylist(song_data, playlist_name)    # download songs from youtube according to the information provided by song_data

if __name__ == "__main__":
    client = SpotifyDownloaderClient(os.path.dirname(sys.argv[0]))
    client.runDownload("spotify:playlist:1Q1uNzJ0ydqEAcnRxYaKri", "Chill Mix")
