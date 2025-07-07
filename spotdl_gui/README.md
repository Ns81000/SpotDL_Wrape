# spotDL GUI Downloader

A graphical user interface for the [spotDL](https://github.com/spotdl/spotdl) music downloader.
This application provides an easy-to-use interface for most of spotDL's common features.

## Features

*   Download songs, albums, playlists, and artist tracks from Spotify.
*   Common download options:
    *   Select output directory.
    *   Choose audio format (mp3, m4a, flac, opus, wav, aac, or custom).
    *   Specify bitrate (including "best available" or custom).
    *   Control embedding of lyrics and metadata (album art, track info).
    *   Toggle SponsorBlock integration (for YouTube sources).
    *   Define overwrite behavior for existing files (skip, force, metadata).
    *   Set the number of concurrent download threads.
*   Advanced options:
    *   Use an archive file to skip already downloaded songs.
    *   Provide a custom search query for non-Spotify URLs or when Spotify matching is poor.
    *   Pass additional raw arguments directly to spotDL.
*   Save track/playlist metadata to `.spotdl` files.
*   Sync local music library with a Spotify playlist (downloads new songs, can be configured to remove deleted ones via spotDL's capabilities, though this GUI focuses on download/update).
*   Get direct download URLs from YouTube Music (or other sources spotDL uses) for Spotify tracks.
*   Real-time output log to see `spotdl`'s progress and messages.
*   Status bar for quick operational feedback.

## Prerequisites

Before running the spotDL GUI Downloader, you need to have the following installed:

1.  **Python 3**: Make sure you have Python 3.7 or newer installed. You can download it from [python.org](https://www.python.org/).
2.  **spotDL**: The core command-line tool. Install it via pip:
    ```bash
    pip install spotdl
    ```
    It's highly recommended to install `spotDL` in a Python virtual environment.
3.  **FFmpeg**: Required by `spotDL` for audio processing (e.g., converting to MP3, embedding metadata).
    *   You can try to let `spotDL` download it for you by running:
        ```bash
        spotdl --download-ffmpeg
        ```
    *   Alternatively, download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html) and ensure it's added to your system's PATH.

## How to Run

1.  **Navigate to the GUI directory**:
    Open your terminal or command prompt and change to the `spotdl_gui` directory:
    ```bash
    cd path/to/your_project/spotdl_gui
    ```
2.  **Run the application**:
    Execute the `app.py` script using Python:
    ```bash
    python app.py
    ```
    If you are using a virtual environment, make sure it is activated before running the script.

## Using the GUI

1.  **Spotify URLs**:
    *   Enter one or more Spotify URLs (for tracks, albums, playlists, or artists) into the "Spotify URLs" field. You can separate multiple URLs with spaces or newlines.
    *   For the "Sync Playlist/Album" feature, this field should contain either a single Spotify playlist/album URL or the path to a local `.spotdl` file.

2.  **Download Options**:
    *   **Output Directory**: Specify where downloaded files should be saved. Click "Browse..." to select a folder. Defaults to a `spotdl_downloads` subfolder in the current working directory.
    *   **Audio Format**: Choose your desired audio format. If "custom" is selected, an entry field will appear for you to type the format (e.g., `ogg`).
    *   **Bitrate**: Select the audio bitrate. "0 (best)" aims for the highest available quality. If "custom" is selected, an entry field will appear.
    *   **Download Threads**: Number of songs to download simultaneously.
    *   **Overwrite Existing Files**: How to handle files that already exist in the output directory.
    *   **Checkboxes**:
        *   `Embed Lyrics`: Include lyrics in the audio file if available.
        *   `Embed Metadata`: Include album art, track title, artist, etc.
        *   `Enable SponsorBlock`: Skip sponsored segments in YouTube videos if YouTube is used as a source.

3.  **Advanced/Specific Options**:
    *   **Save/Sync State File**:
        *   For "Save Metadata": Specify the `.spotdl` file where metadata will be saved.
        *   For "Sync Playlist/Album" (when syncing a URL): Optionally specify a `.spotdl` file to store sync state, enabling faster future syncs. If syncing an existing `.spotdl` file, this field is usually not needed as the source file is updated.
    *   **Archive File**: Specify a `.txt` file. Songs listed in this file will be skipped during download operations.
    *   **Custom Search Query**: If `spotdl` struggles to find a song, or for non-Spotify URLs, you can provide a search query like "Artist - Title".
    *   **Additional spotDL Arguments**: Pass any other valid `spotdl` command-line arguments. Use quotes for arguments containing spaces (e.g., `--ffmpeg-args "-vn"`).

4.  **Action Buttons**:
    *   **Download Songs**: Downloads the specified Spotify URLs using the selected options.
    *   **Save Metadata**: Saves metadata for the given Spotify URLs to the specified "Save/Sync State File".
    *   **Sync Playlist/Album**: Syncs a local directory with a Spotify playlist/album or a `.spotdl` file. Uses the common download options for any new songs.
    *   **Get Direct URLs**: Shows the direct download URLs that `spotdl` would use, without actually downloading the audio.
    *   **Clear Log**: Clears the content of the output log.

5.  **Output Log**:
    *   Displays real-time messages, progress, and errors from `spotdl`.

6.  **Status Bar**:
    *   Shows the current state of the application (e.g., "Ready", "Download in progress...", "Download Failed.").

## Notes

*   The application attempts to check for `spotdl` and `ffmpeg` on startup and will log messages to the console if they are not found.
*   Long operations (like downloading large playlists) are run in a separate thread to keep the GUI responsive. Action buttons will be disabled during these operations.
*   For detailed information on `spotdl` commands and options, refer to the official [spotDL documentation](https://spotdl.readthedocs.io/).

---

This GUI aims to make `spotDL` more accessible. Enjoy your music!
