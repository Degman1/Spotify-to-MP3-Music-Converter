"""Original Version of downloader, veiw the SpotifyDownloaderClient class for an updated version
Credit to the creator of spotify_album_downloader on github
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

with open('settings.json') as data_file:
    settings = json.load(data_file)

client_credentials_manager = SpotifyClientCredentials(client_id=settings['spotify']['client_id'], client_secret=settings['spotify']['client_secret'])
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
sp.trace=False




def chunks(l, n):
    # Thanks to http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def stripString(text):
    return "".join([i for i in text if i not in [i for i in '/\\:*?"><|']])

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

def downloadYoutubeToMP3(link):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'logger': MyLogger(),
            'progress_hooks': [my_hook]
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            a = ydl.download([link])
        return True
    except Exception as e:
        print (repr(e))
        return False


song_data = {} # song_data[uri] = {'artist':x, 'album':x, 'title':x, 'ablum_art':x, 'track':x}
individual_songs = []

#uri = input("Enter playlist uri...")
uri = "spotify:user:dgredsox:playlist:1Q1uNzJ0ydqEAcnRxYaKri"

start_time = time.time()

username = uri.split(':')[2]
playlist_id = uri.split(':')[4]
playlist_name = input("New Playlist Name...")       #TODO handle user not inputting + other errors
offset = 0
results = sp.user_playlist_tracks(username, playlist_id, offset=offset)
individual_songs += results['items']


if not os.path.exists(os.getcwd() + "/output/"):        #make sure the output dir is there
    os.makedirs(os.getcwd() + "/output/")
if not os.path.exists(os.getcwd() + "/output/" + playlist_name + "/"):    #make new dir for individual playlist
    os.makedirs(os.getcwd() + "/output/" + playlist_name)


while (results['next'] != None):
    offset += 100
    results = sp.user_playlist_tracks(username, playlist_id, offset=offset)
    individual_songs += results['items']


"""def validateFilePath(str):
    '''places a "\ " in place of a space to make file path valid'''
    prevIndex = 0
    result = str
    while True:
        index = result[prevIndex:].find(" ")
        if index == -1:
            print(result)
            return result
        elif index == 0 or result[index - 1] != "\\":
            index += prevIndex  #make up for removal of first part of string
            result = result[:index ] + "\\" + result[index:]
            prevIndex = index + 2   #+1 for the next char, +1 for the added backslash"""

individual_songs_temp = []
path = "output/" + playlist_name + "/history.txt"
file = open(path, "r+")
data = file.read()
print("Download History: \n" + data)
for song in individual_songs:
    name = song['track']['album']['name']
    if name not in data:
        individual_songs_temp += song
        file.write("name")
    else:
        print("The song " + name + " is already downloaded into the playlist " + playlist_name)

file.close()
individual_songs = individual_songs_temp

for song in individual_songs:
    song = song['track']
    song_data[song['uri']] = {'artist' : song['artists'][0]['name'],
                              'album' : song['album']['name'],
                              'title' : song['name'],
                              'ablum_art' : song['album']['images'][0]['url'],
                              'track' : str(song['track_number'])}

counter = 0

for song in song_data:
    try:
        print ("")
        counter += 1
        print("Fetching song " + str(counter) + " out of " + str(len(song_data)))
        search_term = song_data[song]['artist'] + " " + song_data[song]['title'] + " lyrics"
        Search_URL = ''.join([i for i in filter(lambda x: x in set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r\x0b\x0c'), "https://www.youtube.com/results?search_query=" + '+'.join(search_term.replace("&", "%26").replace("=", "%3D").replace("*", "%3D").split(" ")))])

        print ("Getting " + Search_URL)
        page = urllib.request.urlopen(Search_URL)
        soup = BeautifulSoup(page.read(), "html.parser")
        search_page = soup.find_all('ol', 'item-section')[0]
        results = soup.find_all('div', 'yt-lockup-dismissable')
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
            continue

        files_in_cd = os.listdir(os.getcwd())
        for i in files_in_cd:
            if i.endswith(".mp3"):
                os.remove(os.getcwd() + "/" + i)
        for i in range(5):
            a = downloadYoutubeToMP3(video_URL)
            if not a:
                print ("Video download attempt " + str(i + 1) + " failed")
            else:
                break
        if not a:
            print ("Failed on: " + song_data[song]['artist'] + "  - " + song_data[song]['title'])
            continue
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

        title = stripString(song_data[song]['title'])
        artist = stripString(song_data[song]['artist'])
        album = stripString(song_data[song]['album'])

        #Already doing this above... no need to do it again
        #if os.path.exists(os.getcwd() + "/output/" + playlist_name + "/" + stripString(artist + " - " + title + ".mp3")):
        #    print("The directory " + playlist_name + " already contains the downloaded song")
        #    continue
        
        try:
            os.rename(file, (os.getcwd() + "/output/" + playlist_name + "/" + stripString(artist + " - " + title + ".mp3")))
            print ("Saved at: " + os.getcwd() + "/output/" + playlist_name + "/" + stripString(artist + " - " + title + ".mp3"))
        except Exception as e:
            print ("Could not rename")
            print (repr(e))
            for i in range(10):
                try:
                    print ("Attempting: " + os.getcwd() + "/output/" + playlist_name + "/" + stripString(artist + " - " + title + "(" + str(i+1) + ").mp3"))
                    os.rename(file, os.getcwd() + "/output/" + playlist_name + "/" + stripString(artist + " - " + title + "(" + str(i+1) + ").mp3"))
                    print ("Saved at: " + os.getcwd() + "/output/" + stripString(artist + " - " + title + "(" + str(i+1) + ").mp3"))
                    break
                except Exception as ex:
                    print ("Rename Error on " + i + ": " + str(repr(ex)))
            else:
                print ("Could not rename (2nd layer)")
                os._exit(5)
    except Exception as e:
        print("Some error happened somewhere????")
        print (e)
        x = input("Hit enter to continue downloading other songs from the playlist...")

print("\nComplete")
