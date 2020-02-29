import os

from SpotifyDownloaderClient import SpotifyDownloaderClient

class SpotifyDownloaderUI:
    client = SpotifyDownloaderClient()
    current_playlist = None

    def __init__(self):
        if not os.path.exists(os.getcwd() + "/output/"):   #make sure the output dir is there
            os.makedirs(os.getcwd() + "/output/")
    
    def printHelpMessage(self):
        desc = "Commands:\n"
        desc += "  help                       -- prints out a list of commands\n"
        desc += "  setp [playlist_name]       -- set current playlist to [playlist_name]; won't create the\n"
        desc += "                                coresponding directory until songs are downloaded to the [playlist_name]\n"
        desc += "  printp                     -- prints out a list of available playlists, indicating which is selected\n"
        desc += "  dp [URI]                   -- downloads the playlist specified by the spotify playlist [URI]\n"
        desc += "                                (found by clicking the three dots next to the play button on\n"
        desc += "                                the spotify app) into the directory ./output/current_playlist\n"
        desc += "                                set using the command setp\n"
        desc += "  rm [filename]              -- removes file [filename] from the current playlist\n"
        desc += "  contents                   -- prints out the contents of the current playlist\n"
        desc += "  quit                       -- quits the SpotifyDownloader program"
        print(desc)
    
    def setWorkingPlaylist(self, cmdLine):
        self.current_playlist = " ".join(cmdLine)[5:]
    
    def printWorkingPlaylists(self):
        '''search through the directories in output to find all the current playlists'''
        playlists = os.listdir(os.getcwd() + "/output/")
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
        path = os.getcwd() + "/output/" + self.current_playlist + "/" + f
        os.remove(path)
        
        #Now, remove it from contents.txt
        file = open(os.getcwd() + "/output/" + self.current_playlist +  "/contents.txt", "r")
        contents = file.read().split("\n")
        file.close()

        newHistory = ""
        for song_info in contents:
            if f not in song_info and song_info != "":
                newHistory += song_info + "\n\n"
        
        file = open(os.getcwd() + "/output/" + self.current_playlist +  "/contents.txt", "w")     #clears the contents of the file when open in write
        file.write(newHistory)
        file.close()
    
    def downloadPlaylist(self, URI):
        if self.current_playlist is  None:
            print("ERROR: Please first set a working playlist")
            return
        self.client.runDownload(URI, self.current_playlist)

    def printContents(self):
        if self.current_playlist is None:
            print("ERROR: Please first set a working playlist")
            return

        if not os.path.exists(os.getcwd() + "/output/" + self.current_playlist + "/contents.txt"):   #make sure the output dir is there
            open(os.getcwd() + "/output/" + self.current_playlist + "/contents.txt", 'a')
        file = open(os.getcwd() + "/output/" + self.current_playlist + "/contents.txt", "r")
        print(file.read())
        file.close()

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
        elif cmd == "setp":
            if self.checkArgs(cmdLine, 1, True): self.setWorkingPlaylist(cmdLine)
        elif cmd == "printp":
            if self.checkArgs(cmdLine, 0): self.printWorkingPlaylists()
        elif cmd == "rm":
            if self.checkArgs(cmdLine, 1, True): self.removeFile(cmdLine)
        elif cmd == "dp":
            if self.checkArgs(cmdLine, 1): self.downloadPlaylist(cmdLine[1])
        elif cmd == "contents":
            if self.checkArgs(cmdLine, 0): self.printContents()
        else: print("ERROR: No such command as " + cmd)

    def run(self):
        '''run the spotify downloader client'''
        print("Welcome to the SpotifyDownloader portal. Type \"help\" for a list of commands.")
        user_input = input("> ")
        while user_input != "quit":
            self.parseInput(user_input.split(" "))
            user_input = input("> ")

if __name__ == "__main__":
    ui = SpotifyDownloaderUI()
    ui.run()