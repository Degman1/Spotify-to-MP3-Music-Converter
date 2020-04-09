"""
SpotifyDownloaderUI to create the user interface for the program and handle the various methods of
SpotifyDownloaderClient in relation to their UI commands

When running in terminal, you must use the sudo command to be able to have admin access

"""

import os
import sys

from SpotifyDownloaderClient import SpotifyDownloaderClient

runAsExec = False       #WARNING: Don't forget to change this if creating an exec file

class SpotifyDownloaderUI:
    current_playlist = None

    def __init__(self):
        if runAsExec:
            self.cwd = os.path.dirname(sys.argv[0])    #Use this for running from executable
        else:
            self.cwd = os.getcwd()                      #Use this for simple script running from terminal
        self.client = SpotifyDownloaderClient(self.cwd)

        if not os.path.exists(self.cwd + "/output/"):   #make sure the output dir is there
            os.makedirs(self.cwd + "/output/")

    def printHelpMessage(self):
        desc = "Commands:\n"
        desc += "  help                              -- prints out a list of commands\n"
        desc += "  setPlaylist [playlist_name]       -- set current playlist to [playlist_name]; won't create the\n"
        desc += "                                       coresponding directory until songs are downloaded to the [playlist_name]\n"
        desc += "  printPlaylists                    -- prints out a list of available playlists, indicating which is selected\n"
        desc += "  printRCP                          -- prints out all the playlists altered during the current running session of the downloader\n"
        desc += "  printPath                         -- prints out the current working directory for playlists\n"
        desc += "  downloadSong [URL] [song_name]    -- downloads the song located at the provided web URL\n"
        desc += "  downloadPlaylist [URI]            -- downloads the playlist specified by the spotify playlist [URI]\n"
        desc += "  setURI [URI]                      -- sets the current playlist URI located in uri.txt to [URI]\n"
        desc += "  printURI [URI]                    -- prints out the current playlist URI\n"
        desc += "  updatePlaylist                    -- updates the playlist specified by the URI located in a text file under the playlist folder\n"
        desc += "                                       (found by clicking the three dots next to the play button on\n"
        desc += "                                       the spotify app) into the directory ./output/current_playlist\n"
        desc += "                                       set using the command setp\n"
        desc += "  rm [filename]                     -- removes file [filename] from the current playlist\n"
        desc += "  contents                          -- prints out the contents of the current playlist\n"
        desc += "  quit                              -- quits the SpotifyDownloader program"
        print(desc)
    
    def setWorkingPlaylist(self, cmdLine):
        p = " ".join(cmdLine)[12:]
        if p != "":
            self.current_playlist = " ".join(cmdLine)[12:]
        else:
            print("ERROR: Please input a valid playlist name")
        
        self.printWorkingPlaylists()
    
    def printWorkingPlaylists(self):
        '''search through the directories in output to find all the current playlists'''
        playlists = os.listdir(self.cwd + "/output/")
        if len(playlists) == 0:
            print("There are not yet any playlists in the output directory")
        for playlist in playlists:
            if playlist == self.current_playlist:
                print("* %s" % playlist)
            elif playlist[0] != ".":    #don't include other hidden files, only veiwable directories
                print("  %s" % playlist)
    
    def removeFile(self, cmdLine):
        if self.current_playlist is None:
            print("ERROR: Please first set a working playlist")
            return

        f = " ".join(cmdLine)[3:]
        path = self.cwd + "/output/" + self.current_playlist + "/" + f
        if os.path.exists(path):
            os.remove(path)
        else:
            print("ERROR: No such file or directory: \"%s\"" % path)
    
    def downloadPlaylist(self, URI):
        path = self.cwd + "/output/" + self.current_playlist
        if os.path.exists(path):
            URIFile = open(path + "/uri.txt", "w")    #update URI in text file
            URIFile.write(URI)
            URIFile.close()

        if self.current_playlist is  None:
            print("ERROR: Please first set a working playlist")
            return
        self.client.runDownload(URI, self.current_playlist)

    def downloadSong(self, video_URL, song_name):
        if self.current_playlist is  None:
            print("ERROR: Please first set a working playlist")
            return
        self.client.downloadIndividualSong(video_URL, song_name, self.current_playlist)

    def printContents(self):
        if self.current_playlist is None:
            print("ERROR: Please first set a working playlist")
            return
        c = self.client.getContents(self.current_playlist)
        if c is not None:
            print("\nThe current playlist contains %s songs:" % len(c) + "\n")
            print( "\t" + "\n\t".join(c) )
        else:
            print("ERROR: The current playlist does not yet exist in the output directory")

    def printRCP(self):
        print(str(len(self.client.rcp)) + " playlist(s) have been changed:")
        for playlist, songs in self.client.rcp.items():
            print("\n  " + playlist + "-")
            for s in songs:
                print("    " + s)

    def updatePlaylist(self):
        URI = None
        URIpath = self.cwd + "/output/" + self.current_playlist + "/uri.txt"

        if os.path.exists(URIpath):
            URIFile = open(URIpath, "r")
            URI = URIFile.read()
        else:
            URIFile = open("uri.txt", "w")
            URI = input("Enter playlist URI (saves URI after the first time it is entered): ")
            URIFile.write(URI)
            if os.path.exists(self.cwd + "/uri.txt"):
                os.rename(self.cwd + "/uri.txt", URIpath)
            else:
                print("ERROR: Could not properly move \'uri.txt\' into its apropriate playlist folder")
            
        URIFile.close()
        if URI is None:
            print("ERROR: Could not obtain the proper URI. Please attempt the downloadPlaylist command instead.")
        else:
            self.client.runDownload(URI, self.current_playlist)

    def setURI(self, URI):
        if self.current_playlist is  None:
            print("ERROR: Please first set a working playlist")
            return

        URIpath = self.cwd + "/output/" + self.current_playlist + "/uri.txt"
        URIFile = open(URIpath, "w")
        URIFile.write(URI)
        URIFile.close()

    def printURI(self):
        if self.current_playlist is  None:
            print("ERROR: Please first set a working playlist")
            return

        URIpath = self.cwd + "/output/" + self.current_playlist + "/uri.txt"

        if os.path.exists(URIpath):
            URIFile = open(URIpath, "r")
            print(URIFile.read())
            URIFile.close()
        else:
            print("ERROR: No saved spotify URI for the current playlist")

    def checkArgs(self, cmdLine, expected, andGreater=False):
        '''Garuntees the number of args provided are correct for the given command'''
        args = len(cmdLine) - 1
        if andGreater and args >= expected:
            return True
        elif (not andGreater) and args != expected:
            print("ERROR: Incorect number of arguments. Expected %s not %s args for cmd %s" % (expected, args, cmdLine[0]))
            return False
        return True
    
    def parseInput(self, cmdLine):
        cmd = cmdLine[0].lower()
        if cmd == "help":
            if self.checkArgs(cmdLine, 0): self.printHelpMessage()
        elif cmd == "setplaylist":
            if self.checkArgs(cmdLine, 1, True): self.setWorkingPlaylist(cmdLine)
        elif cmd == "printplaylists":
            if self.checkArgs(cmdLine, 0): self.printWorkingPlaylists()
        elif cmd == "rm":
            if self.checkArgs(cmdLine, 1, True): self.removeFile(cmdLine)
        elif cmd == "downloadplaylist":
            if self.checkArgs(cmdLine, 1): self.downloadPlaylist(cmdLine[1])
        elif cmd == "contents":
            if self.checkArgs(cmdLine, 0): self.printContents()
        elif cmd == "printpath":
            if self.checkArgs(cmdLine, 0) and self.current_playlist is not None:
                    print(self.cwd + "/output/" + self.current_playlist + "/")
            else:
                print("ERROR: A current playlist must be selected before a path can be displayed")
        elif cmd == "downloadsong":
            if self.checkArgs(cmdLine, 2): self.downloadSong(cmdLine[1], cmdLine[2])
        elif cmd == "printrcp":
            if self.checkArgs(cmdLine, 0): self.printRCP()
        elif cmd == "updateplaylist":
            if self.checkArgs(cmdLine, 0): self.updatePlaylist()
        elif cmd == "seturi":
            if self.checkArgs(cmdLine, 1): self.setURI(cmdLine[1])
        elif cmd == "printuri":
            if self.checkArgs(cmdLine, 0): self.printURI()
        else: print("ERROR: No such command as " + cmd)

    def run(self):
        '''run the spotify downloader client'''
        print("\nWelcome to the SpotifyDownloader portal. Type \"help\" for a list of commands.")
        user_input = input("> ")
        while user_input != "quit":
            try:
                self.parseInput(user_input.split(" "))
            except Exception as e:
                print(e)
                print("ERROR: Continued session despite the crash...")
            print("\n__________________________________________")
            user_input = input("> ")

if __name__ == "__main__":
    ui = SpotifyDownloaderUI()
    ui.run()