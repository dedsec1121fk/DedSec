# DedSec Radio Script

A terminal-based music player script that lets you create a custom radio station from your own music collection. The script plays music from various directories (stations), allowing users to shuffle and play audio files in formats like MP3, WAV, and FLAC. It uses `termux-media-player` to handle the playback on a Termux environment.

## Features

- **Station Selection**: Choose from a list of music stations, where each station is represented by a folder containing audio files.
- **Shuffle Play**: Songs are shuffled before playback to ensure variety each time you choose a station.
- **Playback Control**: Options to stop the music, continue to the next song, or return to the station selection menu.
- **Restart Playlists**: Once all songs in a station have been played, the playlist restarts and shuffles the songs again.
- **User-Friendly Interface**: Simple command-line interface with easy-to-follow prompts and options.

## Requirements

To run this script, you'll need the following:

- **Python 3.x**: The script is written in Python, so you'll need Python installed on your system.
- **Termux (Android)**: The script uses `termux-media-player` to play audio files, which is available in Termux. You need to install Termux on your Android device to use this script.
- **Supported Audio Formats**: The script supports MP3, WAV, and FLAC file formats.

## How It Works

- **Station List**: When you run the script, it will automatically scan the `~/DedSec/Radio` directory and display the list of available stations (folders).
- **Shuffle and Play**: Upon selecting a station, the script will shuffle the songs within that folder and begin playback using `termux-media-player`.
- **Playback Control**: While listening, you can:
  - **Stop** the music by pressing `[S]`.
  - **Continue** to the next song by pressing `[C]`.
  - **Go Back** to the station selection by pressing `[B]`.
  - **Exit** the radio entirely by pressing `[E]`.
  
If all songs in a station have been played, the playlist will restart with a new shuffle.

## Error Handling

- **Invalid Input**: If you enter an invalid number when choosing a station or a command during playback, the script will prompt you again to make a valid selection.
- **Empty Station Folders**: If a folder doesn't contain any valid audio files (MP3, WAV, or FLAC), the script will notify you and return you to the station selection screen.
- **No Stations Available**: If there are no folders inside the `~/DedSec/Radio` directory, the script will notify you that no stations are available and exit.

## Customizing Your Radio Stations

You can personalize your radio experience by:

- Adding as many folders (stations) as you like within the `~/DedSec/Radio` directory.
- Organizing the audio files however you prefer—songs can be in any order and will be shuffled every time.
- Changing the interface of the script to add more features, such as volume control or additional file formats.

## Troubleshooting

- **Termux Media Player Not Working**: Ensure you have Termux installed and the `termux-api` package is up-to-date.
- **Audio Not Playing**: Double-check that your audio files are in supported formats (MP3, WAV, or FLAC).
- **Permission Errors**: Make sure you have the necessary permissions to read files in the `~/DedSec/Radio` directory and execute `termux-media-player`.