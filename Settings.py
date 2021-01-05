""" File to hold the global settings of this project """

class Settings:
    BUILD_EXECUTABLE = True   # Taylors file management method to the program being run as a Python file or an executable
    DEBUG_MODE = not BUILD_EXECUTABLE    # Incorperates the Python error message into the system's error printing