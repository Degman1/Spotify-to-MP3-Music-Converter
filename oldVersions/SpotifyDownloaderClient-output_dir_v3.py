"""
SpotifyDownloaderClient to handle the downloading of songs retrieving data from spotify, downloading the 
songs off of youtube, and converting them into mp3 files. Credit to the creator of spotify_album_downloader.py on 
github
"""

import json
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import time

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error, TYER
from mutagen.easyid3 import EasyID3
import youtube_dl
import urllib.request
from bs4 import BeautifulSoup
import os

class SpotifyDownloaderClient:
    sp = None   #holds spotify client credentials

    def __init__(self):
        with open('settings.json') as data_file:
            settings = json.load(data_file)
        
        client_credentials_manager = SpotifyClientCredentials(client_id=settings['spotify']['client_id'], client_secret=settings['spotify']['client_secret'])
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        self.sp.trace = False
    
    @staticmethod
    def announceCompletion(str):
        print("****" + str)
    
    @staticmethod
    def stripString(text):
        return "".join([i for i in text if i not in [i for i in '/\\:*?"><|']])
    
    @staticmethod
    def my_hook(d):
        if '_percent_str' in d:
            if d['status'] == 'downloading':
                print ("\r" + d['_percent_str'], end='')
        if d['status'] == 'finished':
                print ('\rDone downloading, now converting ...')
    
    class MyLogger(object):
        def debug(self, msg):
            pass

        def warning(self, msg):
            pass

        def error(self, msg):
            print (msg)

    def downloadYoutubeToMP3(self, link):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'logger': self.MyLogger(),
                'progress_hooks': [SpotifyDownloaderClient.my_hook]
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                a = ydl.download([link])
            return True
        except Exception as e:
            print (repr(e))
            return False
    
    def directorySetup(self, playlist_name):
        if not os.path.exists(os.getcwd() + "/output/"):                          #make sure the output dir is there
            os.makedirs(os.getcwd() + "/output/")
        if not os.path.exists(os.getcwd() + "/output/" + playlist_name + "/"):    #make new dir for individual playlist
            os.makedirs(os.getcwd() + "/output/" + playlist_name)
        if not os.path.isfile(os.getcwd() + "/output/" + playlist_name + "/contents.txt"):
            open(os.getcwd() + "/output/" + playlist_name + "/contents.txt", "a").close()
        
        SpotifyDownloaderClient.announceCompletion("Directory Setup Successful")

    def filterOutPreDownloadedSongs(self, individual_songs, path):
        individual_songs_temp = []
        # Be careful not to mistake songs with the same 'name' as being the same. They could have the same 
        # general name provided by spotify but still actually be a different song
        
        file = open(path, "r")
        data = file.read()
        file.close()

        for song in individual_songs:
            song_id = song['track']['id']
            song_name = song['track']['name']
            if song_id not in data:
                individual_songs_temp.append(song)
            else:
                print("The song %s (%s) is already downloaded into this playlist" % (song_name, song_id))

        SpotifyDownloaderClient.announceCompletion("Song Filtering Successful")
        return individual_songs_temp

    def retrieveSongData(self, uri, playlist_name):
        individual_songs = []
        song_data = {}

        #ex. spotify:user:18august2004:playlist:1Yukg59UEknAP9ZRum7x3S for mnm playlist
        if len(uri) != 57 and uri.count(":") != 4:
            print("ERROR: The provided URI is not valid")
            return None
        username = uri.split(':')[2]
        playlist_id = uri.split(':')[4]
        offset = 0
        results = self.sp.user_playlist_tracks(username, playlist_id, offset=offset)
        individual_songs += results['items']

        while (results['next'] != None):
            offset += 100
            results = self.sp.user_playlist_tracks(username, playlist_id, offset=offset)
            individual_songs += results['items']
        
        individual_songs = self.filterOutPreDownloadedSongs(individual_songs, "output/" + playlist_name + "/contents.txt")

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

    def getWebpageContents(self, song_data, song):
        search_term = song_data[song]['artist'] + " " + song_data[song]['title'] + " lyrics"
        Search_URL = ''.join([i for i in filter(lambda x: x in set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r\x0b\x0c'), "https://www.youtube.com/results?search_query=" + '+'.join(search_term.replace("&", "%26").replace("=", "%3D").replace("*", "%3D").split(" ")))])

        print ("Getting " + Search_URL)
        page = urllib.request.urlopen(Search_URL)
        soup = BeautifulSoup(page.read(), "html.parser")
        #search_page = soup.find_all('ol', 'item-section')[0]
        return soup.find_all('div', 'yt-lockup-dismissable')

    def downloadSong(self, song_data, song, playlist_name):
        try:
            print ("")

            results = self.getWebpageContents(song_data, song)

            for tile in results:
                try:
                    link = tile.find_all('a')[0]['href']
                    if "&list=" in link:
                        continue
                    else:
                        print ("Video link = https://www.youtube.com" + link)
                        video_URL = "https://www.youtube.com" + link
                        break
                except:
                    print ("ERROR GETING YOUTUBE URL")
            else:
                video_URL = "Error"
            if video_URL == "Error":
                print ("Failed on: " + song_data[song]['artist'] + "  - " + song_data[song]['title'])
                return

            files_in_cd = os.listdir(os.getcwd())
            for i in files_in_cd:
                if i.endswith(".mp3"):
                    os.remove(os.getcwd() + "/" + i)
            for i in range(5):
                a = self.downloadYoutubeToMP3(video_URL)
                if not a:
                    print ("Video download attempt " + str(i + 1) + " failed")
                else:
                    break
            if not a:
                print ("Failed on: " + song_data[song]['artist'] + "  - " + song_data[song]['title'])
                return
            print ("Download Complete")
            files_in_cd = os.listdir(os.getcwd())
            for i in files_in_cd:
                if i.endswith(".mp3"):
                    file = os.getcwd() + "/" + i
            try:
                print ("Tagging /" + file.split("/")[-1])
            except:
                print ("Tagging (Special charaters in name)")

            audio = MP3(file, ID3=ID3)
            
            try:
                audio.add_tags()
            except error:
                pass
            urllib.request.urlretrieve(song_data[song]['ablum_art'], (os.getcwd() + "/TempAArtImage.jpg"))
            audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc=u'cover', data=open(os.getcwd() + "/TempAArtImage.jpg", 'rb').read()))
            audio.save()
            os.remove(os.getcwd() + "/TempAArtImage.jpg")
            audio = EasyID3(file)
            audio["tracknumber"] = song_data[song]['track']
            audio["title"] = song_data[song]['title']
            audio["album"] = song_data[song]['album']
            audio["artist"] = song_data[song]['artist']
            audio.save()

            title = SpotifyDownloaderClient.stripString(song_data[song]['title'])
            artist = SpotifyDownloaderClient.stripString(song_data[song]['artist'])
            #album = SpotifyDownloaderClient.stripString(song_data[song]['album'])

            #rename the mp3 file to put it in the correct directory
            try:
                name = SpotifyDownloaderClient.stripString(artist + " - " + title + ".mp3")
                os.rename(file, (os.getcwd() + "/output/" + playlist_name + "/" + name))
                print ("Saved at: " + os.getcwd() + "/output/" + playlist_name + "/" + name)

                file = open(os.getcwd() + "/output/" + playlist_name + "/contents.txt", "a")
                file.write("%s (id: %s): %s\n\n" % (song_data[song]['name'], song_data[song]['id'], name))
                file.close()

            except Exception as e:
                print ("Could not rename")
                print (repr(e))
                for i in range(10):
                    try:
                        name = SpotifyDownloaderClient.stripString(artist + " - " + title + "(" + str(i+1) + ").mp3")
                        print ("Attempting: " + os.getcwd() + "/output/" + playlist_name + "/" + name)
                        os.rename(file, os.getcwd() + "/output/" + playlist_name + "/" + name)
                        print ("Saved at: " + os.getcwd() + "/output/" + name)

                        file = open(os.getcwd() + "/output/" + playlist_name + "/contents.txt", "a")
                        file.write("%s (id: %s): %s\n\n" % (song_data[song]['name'], song_data[song]['id'], name))
                        file.close()
                        break
                    except Exception as ex:
                        print ("Rename Error on " + i + ": " + str(repr(ex)))
                else:
                    print ("Could not rename (2nd layer)")
                    os._exit(5)
            

        except Exception as e:
            print("Some error happened somewhere")
            print (e)
            x = input("Hit enter to continue downloading other songs from the playlist...")
    
    def downloadPlaylist(self, song_data, playlist_name):
        for song in song_data:
            self.downloadSong(song_data, song, playlist_name)
        
        SpotifyDownloaderClient.announceCompletion("Downloads Complete (attempted total of %s)" % len(song_data))

    def runDownload(self, uri, playlist_name):
        self.directorySetup(playlist_name)                      # setup correct directories required for download
        song_data = self.retrieveSongData(uri, playlist_name)   # retrieve song data from spotify playlist
        if song_data is not None:
            self.downloadPlaylist(song_data, playlist_name)    # download songs from youtube according to the information provided by song_data

if __name__ == "__main__":
    client = SpotifyDownloaderClient()
    client.runDownload("spotify:user:18august2004:playlist:1Yukg59UEknAP9ZRum7x3S", "Chill Mix")
