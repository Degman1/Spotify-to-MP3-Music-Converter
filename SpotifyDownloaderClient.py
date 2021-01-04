"""
SpotifyDownloaderClient to handle the downloading of songs retrieving data from spotify, downloading the 
songs off of youtube, and converting them into mp3 files. Credit for the downloading methods along with various 
peices of the code goes to the creator of spotify_album_downloader.py on github

"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time

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
    def printErrorMessage(message):
        print('\033[91mERROR: ' + message + '\033[0m')
    
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
            pass

        def error(self, msg):
            SpotifyDownloaderClient.printErrorMessage(str(msg))

    def downloadYoutubeToMP3(self, link):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'logger': self.MyLogger(),
                'progress_hooks': [SpotifyDownloaderClient.my_hook],
                'nocheckcertificate': True
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                a = ydl.download([link])
            return True
        except Exception as e:
            print (repr(e))
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


    def downloadIndividualSong(self, video_URL, song_name, playlist_name):
        self.directorySetup(playlist_name)

        files_in_cd = os.listdir(os.getcwd())
        for i in files_in_cd:
            if i.endswith(".mp3"):
                os.remove(self.cwd + "/" + i)
    
        a = self.downloadYoutubeToMP3(video_URL)
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

        name = self.cwd + "/output/" + playlist_name + "/" + song_name + ".mp3"
        
        os.rename(file, (name))
        print("Saved at: " + name)
        print()

    def downloadSong(self, song_data, song, playlist_name):
        try:
            link = self.getVideoURL(song_data, song)
            
            if link == None:
                print ("Failed on: " + song_data[song]['artist'] + "  - " + song_data[song]['title'])
                return 0
            
            print("Video Link = " + link)

            files_in_cd = os.listdir(self.cwd)

            for i in files_in_cd:
                if i.endswith(".mp3"):
                    os.remove(self.cwd + "/" + i)
            for i in range(5):
                a = self.downloadYoutubeToMP3(link)
                if not a:
                    print ("Video download attempt " + str(i + 1) + "/5 failed (make sure youtube-dl is up to date)")
                else:
                    break
            if not a:
                print ("Failed on: " + song_data[song]['artist'] + "  - " + song_data[song]['title'])
                return

            print ("\rDownload and conversion complete")

            files_in_cd = os.listdir(os.getcwd())

            for i in files_in_cd:
                if i.endswith(".mp3"):
                    file = os.getcwd() + "/" + i

            audio = MP3(file, ID3=ID3)
            
            try:
                audio.add_tags()
            except error:
                pass

            urllib.request.urlretrieve(song_data[song]['ablum_art'], (self.cwd + "/TempAArtImage.jpg"))
            audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc=u'cover', data=open(self.cwd + "/TempAArtImage.jpg", 'rb').read()))
            audio.save()
            os.remove(self.cwd + "/TempAArtImage.jpg")
            audio = EasyID3(file)
            audio["tracknumber"] = song_data[song]['track']
            audio["title"] = song_data[song]['title']
            audio["album"] = song_data[song]['album']
            audio["artist"] = song_data[song]['artist']
            audio["genre"] = playlist_name #this allows the user to add the song to the apple music library and create a smart-playlist to only include songs from a certain genre
            audio.save()

            title = SpotifyDownloaderClient.stripString(song_data[song]['title'])
            #artist = SpotifyDownloaderClient.stripString(song_data[song]['artist'])
            #album = SpotifyDownloaderClient.stripString(song_data[song]['album'])

            #rename the mp3 file to put it in the correct directory
            try:
                name = SpotifyDownloaderClient.stripString(title + ".mp3")
                os.rename(file, (self.cwd + "/output/" + playlist_name + "/" + name))
                print ("Saved at " + self.cwd + "/output/" + playlist_name + "/" + name)
                return 1

            except Exception as e:
                print ("Could not rename")
                print (repr(e))
                for i in range(10):
                    try:
                        name = SpotifyDownloaderClient.stripString(artist + " - " + title + "(" + str(i+1) + ").mp3")
                        print ("Attempting: " + self.cwd + "/output/" + playlist_name + "/" + name)
                        os.rename(file, self.cwd + "/output/" + playlist_name + "/" + name)
                        print ("Saved at: " + self.cwd + "/output/" + name)
                        return 1
                    except Exception as ex:
                        print ("Rename Error on " + i + ": " + str(repr(ex)))
                        return 0
                else:
                    print ("Could not rename (2nd layer)")
                    os._exit(5)
                    return 0

        except Exception as e:
            print (e)
            SpotifyDownloaderClient.printErrorMessage("Some error happened somewhere... \nSomething went very wrong... Please contact the program designer for help")
            return 0
    
    def downloadPlaylist(self, song_data, playlist_name):
        total = len(song_data)
        complete_counter = 0

        for song in song_data:
            print("\nStarting song %s/%s:" % (complete_counter + 1, total))

            c = self.downloadSong(song_data, song, playlist_name)

            if c:
                #update the recently changed playlists dictionary
                if playlist_name not in self.rcp.keys():
                    self.rcp[playlist_name] = {song_data[song]['title']}
                else:
                    self.rcp[playlist_name].add(song_data[song]['title'])
            else:
                print("ERROR: Unable to download the song %s" % (song))
            
            complete_counter += 1

        all_songs = os.listdir(self.cwd + "/output/" + playlist_name + "/")
        n_all_songs = len(all_songs)

        if "uri.txt" in all_songs:
            n_all_songs -= 1
        if ".DS_Store" in all_songs:
            n_all_songs -= 1
        
        if total == 0:
            SpotifyDownloaderClient.announceCompletion("Playlist %s is already up to date" % playlist_name)
        else:
            SpotifyDownloaderClient.announceCompletion("Downloads Finished: %s/%s" % (complete_counter, total))
        
        SpotifyDownloaderClient.announceCompletion("There are now %s songs in the playlist %s" % (n_all_songs, playlist_name))
        print()

    def runDownload(self, uri, playlist_name):
        self.directorySetup(playlist_name)                      # setup correct directories required for download
        song_data = self.retrieveSongData(uri, playlist_name)   # retrieve song data from spotify playlist
        if song_data is not None:
            self.downloadPlaylist(song_data, playlist_name)    # download songs from youtube according to the information provided by song_data

if __name__ == "__main__":
    client = SpotifyDownloaderClient(os.path.dirname(sys.argv[0]))
    client.runDownload("spotify:playlist:1Q1uNzJ0ydqEAcnRxYaKri", "Chill Mix")
