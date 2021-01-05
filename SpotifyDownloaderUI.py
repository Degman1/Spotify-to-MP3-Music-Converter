"""
SpotifyDownloaderUI to create the user interface for the program and handle the various methods of
SpotifyDownloaderClient in relation to their UI commands

When running in terminal, use the sudo command to have admin access

"""

import os
import sys

import ffmpeg   #not sure if this import is necessery in the UI file, but just import to make sure pyinstaller notices it
import ffprobe

from SpotifyDownloaderClient import SpotifyDownloaderClient
from Settings import Settings

class SpotifyDownloaderUI:
    current_playlist = None

    def __init__(self):
        if Settings.BUILD_EXECUTABLE:
            self.cwd = os.path.dirname(sys.argv[0])    #Use this for running from executable
        else:
            self.cwd = os.getcwd()                      #Use this for simple script running from terminal
        self.client = SpotifyDownloaderClient(self.cwd)

        if not os.path.exists(self.cwd + "/output/"):   #make sure the output dir is there
            os.makedirs(self.cwd + "/output/")

    def printHelpMessage(self):
        desc = "Commands (case insensitive):\n"
        
        desc += "  help                                     -- prints out a list of commands\n"
        
        desc += "  createPlaylist [URI] [playlist_name]     -- create new playlist [playlist_name] with the corresponding Spotify [URI]\n"
        desc += "  setPlaylist [playlist_name]              -- set current playlist to [playlist_name]\n"
        desc += "  setURI [URI]                             -- sets the current playlist URI located in uri.txt to [URI]\n"

        desc += "  printPlaylists                           -- prints out a list of available playlists, indicating which is selected\n"
        desc += "  printContents                            -- prints out the songs in the current playlist\n"
        desc += "  printRCP                                 -- prints out all the playlists altered during the current app session\n"
        desc += "  printPath                                -- prints out the current working directory for playlists\n"
        desc += "  printURI                                 -- prints out the current playlist URI\n"

        desc += "  downloadYoutubeSong [URL] [file_name]    -- downloads the song located at the provided web [URL] to file name [file_name].mp3\n"
        desc += "  updatePlaylist                           -- updates the playlist specified by the [URI] located in a text file under the\n"
        desc += "                                              playlist folder into the directory ./output/current_playlist\n"
        desc += "  updateAllPlaylists                       -- updates every available playlist that already has an associated URI\n"
        
        desc += "  rm [filename]                            -- removes file [filename] from the current playlist (use to remove a song)\n"
        desc += "  quit                                     -- quits the SpotifyDownloader program\n"
        
        desc += "\nFind the Spotify playlist [URI] by clicking the three dots next to the play button on the desktop Spotify App"
        
        print(desc)

    def createPlaylist(self, args):
        name = " ".join(args[1:])      # reform original command to grab all the words seperated by spaces in the playlist name

        if name in os.listdir(self.cwd + "/output/"):
            SpotifyDownloaderClient.printErrorMessage("This playlist name is already in use, please choose another one to avoid overwriting the existing playlist")
        elif name == "":
            SpotifyDownloaderClient.printErrorMessage("Please input a valid playlist name")
        else:
            self.current_playlist = name
            self.setURI(args[0])
        
        self.printPlaylists()

    def setPlaylist(self, args):
        name = " ".join(args)      # reform original command to grab all the words seperated by spaces in the playlist name
        if name != "" and name in os.listdir(self.cwd + "/output/"):    # make sure the playlist name is valid and actually exists in the output directory
            self.current_playlist = name
        else:
            SpotifyDownloaderClient.printErrorMessage("Please input a valid playlist name")
        
        self.printPlaylists()
    
    def printPlaylists(self):
        '''search through the directories in output to find all the current playlists'''

        playlists = os.listdir(self.cwd + "/output/")
        if len(playlists) == 0:
            print("There are not yet any playlists in the output directory")
        for playlist in playlists:
            if self.current_playlist != None and playlist == self.current_playlist:
                print("* %s" % playlist)
            elif playlist[0] != ".":    #don't include other hidden files, only veiwable directories
                print("  %s" % playlist)
    
    def removeFile(self, cmdLine):
        if self.current_playlist is None:
            SpotifyDownloaderClient.printErrorMessage("Please first set a working playlist")
            return

        f = " ".join(cmdLine)
        path = self.cwd + "/output/" + self.current_playlist + "/" + f
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                if "[Errno 13] Permission denied: " in str(e):
                    SpotifyDownloaderClient.printErrorMessage("Cannot remove the mp3 file. PLEASE ENABLE FILE ACCESS IN YOUR SETTINGS by checking off [ System Preferences > Security and Privacy > Full Disk Access > Terminal ]. Or, use the sudo command if running the program in the terminal.", e = e)
                else:
                    SpotifyDownloaderClient.printErrorMessage("Failed to remove the mp3 file. Please remove it yourself in the finder application", e = e)
        else:
            SpotifyDownloaderClient.printErrorMessage("No such file or directory: \"%s\"" % path)
    
    def downloadYoutubeSong(self, video_URL, file_name):
        if self.current_playlist is  None:
            SpotifyDownloaderClient.printErrorMessage("Please first set a working playlist")
            return
        self.client.downloadIndividualSong(video_URL, file_name, self.current_playlist)

    def printContents(self):
        if self.current_playlist is None:
            SpotifyDownloaderClient.printErrorMessage("Please first set a working playlist")
            return
        c = self.client.getContents(self.current_playlist)
        if c is not None:
            print("\nThe current playlist contains %s songs:" % len(c) + "\n")
            print( "\t" + "\n\t".join(c) )
        else:
            SpotifyDownloaderClient.printErrorMessage("The current playlist does not yet exist in the output directory")

    def printRCP(self):
        if len(self.client.rcp.items()) >= 1:
            print(str(len(self.client.rcp)) + " playlists have been changed this session:")
        else:
            print("No playlists have been changed this session")
        for playlist, songs in self.client.rcp.items():
            print("\n  " + playlist + "-")
            for s in songs:
                print("    " + s)

    def updatePlaylist(self, playlistName):
        if self.current_playlist is None:
            SpotifyDownloaderClient.printErrorMessage("A current playlist must be selected before a path can be displayed")
            return

        uri = self.getURI()
        if uri != None:
            self.client.runDownload(uri, playlistName)
        else:
            SpotifyDownloaderClient.printErrorMessage("Please set a URI for the current playlist first")            

    def updateAllPlaylists(self):
        playlists = os.listdir(self.cwd + "/output/")
        for playlist in playlists:
            if playlist == ".DS_Store":
                continue
            print("Updating playlist %s:" % playlist)
            self.current_playlist = playlist
            URIpath = self.cwd + "/output/" + playlist + "/.uri.txt"
            if not os.path.exists(URIpath):
                print("Playlist %s does not have a preset URI\n" % playlist)
                continue
            self.updatePlaylist(playlist)
        self.current_playlist = None

    def setURI(self, URI):
        if self.current_playlist is  None:
            SpotifyDownloaderClient.printErrorMessage("Please first set a working playlist")
            return

        if "spotify:playlist:" not in URI:
            SpotifyDownloaderClient.printErrorMessage("The URI is invalid (or the playlist name and uri might switched)")
            return

        if not os.path.exists(self.cwd + "/output/" + self.current_playlist):
            os.makedirs(self.cwd + "/output/" + self.current_playlist)
        URIFile = open(self.cwd + "/output/" + self.current_playlist + "/.uri.txt", "w")
        URIFile.write(URI)
        URIFile.close()

    def getURI(self):
        if self.current_playlist is  None:
            SpotifyDownloaderClient.printErrorMessage("Please first set a working playlist")
            return

        URIpath = self.cwd + "/output/" + self.current_playlist + "/.uri.txt"

        if os.path.exists(URIpath):
            URIFile = open(URIpath, "r")
            uri = URIFile.read()
            URIFile.close()
            return uri
        else:
            SpotifyDownloaderClient.printErrorMessage("No saved spotify URI for the current playlist")
            return None
    
    def printURI(self):
        uri = self.getURI()
        if uri != None:
            print(uri)

    def checkArgs(self, cmdLine, expectedNumberArguments, andGreater=False):
        '''Garuntees the number of args provided are correct for the given command'''
        numberArguments = len(cmdLine) - 1
        if andGreater and numberArguments >= expectedNumberArguments:
            return True
        if not andGreater and numberArguments == expectedNumberArguments:
            return True
        
        SpotifyDownloaderClient.printErrorMessage("Incorect number of arguments. Expected %s not %s args for the \"%s\" command" % (expectedNumberArguments, numberArguments, cmdLine[0]))
        return False
    
    def parseInput(self, cmdLine):
        cmd = cmdLine[0]
        if cmd == "help":
            if self.checkArgs(cmdLine, 0): self.printHelpMessage()
        elif cmd == "createplaylist":
            if self.checkArgs(cmdLine, 2, True): self.createPlaylist(cmdLine[1:])
        elif cmd == "setplaylist":
            if self.checkArgs(cmdLine, 1, True): self.setPlaylist(cmdLine[1:])
        elif cmd == "printplaylists":
            if self.checkArgs(cmdLine, 0): self.printPlaylists()
        elif cmd == "rm":
            if self.checkArgs(cmdLine, 1, True): self.removeFile(cmdLine[1:])
        elif cmd == "printcontents":
            if self.checkArgs(cmdLine, 0): self.printContents()
        elif cmd == "printpath":
            if self.checkArgs(cmdLine, 0) and self.current_playlist is not None:
                    print(self.cwd + "/output/" + self.current_playlist + "/")
            else:
                SpotifyDownloaderClient.printErrorMessage("A current playlist must be selected before a path can be displayed")
        elif cmd == "downloadyoutubesong":
            if self.checkArgs(cmdLine, 2): self.downloadYoutubeSong(cmdLine[1], cmdLine[2])
        elif cmd == "printrcp":
            if self.checkArgs(cmdLine, 0): self.printRCP()
        elif cmd == "updateplaylist":
            if self.checkArgs(cmdLine, 0): self.updatePlaylist(self.current_playlist)
        elif cmd == "updateallplaylists":
            if self.checkArgs(cmdLine, 0): self.updateAllPlaylists()
        elif cmd == "seturi":
            if self.checkArgs(cmdLine, 1): self.setURI(cmdLine[1])
        elif cmd == "printuri":
            if self.checkArgs(cmdLine, 0): self.printURI()
        else: SpotifyDownloaderClient.printErrorMessage("No such command as \"" + cmd + "\"")

    def run(self):
        '''run the spotify downloader client'''
        print("\nWelcome to the SpotifyDownloader portal. Type \"help\" for a list of commands.")
        
        user_input = input("> ").strip().split(" ")
        if len(user_input) > 0:     # only change the command to lowercase for parsing
            user_input[0] = user_input[0].lower()

        # I hate it when you can't figure out how to quit a program easily (ehem vim), so make it super intuitive for the user
        while user_input[0] != "quit" and user_input[0] != "quit()" and user_input[0] != "q" and user_input[0] != "end" and user_input[0] != "terminate" and user_input[0] != "close" and user_input[0] != "exit":
            if user_input != "":
                try:
                    self.parseInput(user_input)
                except Exception as e:
                    SpotifyDownloaderClient.printErrorMessage("Failed to complete the requested command operation", e)
                print("\n__________________________________________")
            user_input = input("> ").strip().split(" ")
            if len(user_input) > 0:     # only change the command to lowercase for parsing
                user_input[0] = user_input[0].lower()

if __name__ == "__main__":
    ui = SpotifyDownloaderUI()
    ui.run()