import subprocess
import os
import sys
import shlex
import re
from pathlib import Path
from typing import List, Tuple, Optional

# --- Helper Functions for User Interaction and Validation ---

def run_command(command_parts: List[str]) -> Tuple[int, List[str]]:
    """
    Executes a shell command (provided as a list of parts), streams its output,
    and collects all output lines.
    Returns a tuple: (return_code, collected_output_lines).
    """
    collected_lines = []
    try:
        # Using shell=False is crucial for security and explicit argument handling.
        # This prevents shell injection vulnerabilities and ensures arguments are passed
        # exactly as intended, even if they contain spaces or special characters.
        process = subprocess.Popen(
            command_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout for unified output
            text=True,                 # Decode stdout/stderr as text
            bufsize=1                  # Line-buffered output
        )

        # Stream output in real-time and collect
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
            collected_lines.append(line.strip())

        process.stdout.close()
        return_code = process.wait()

        if return_code != 0:
            print(f"\n--- Command Failed with Exit Code {return_code} ---")
            print(f"Executed Command: {' '.join(shlex.quote(arg) for arg in command_parts)}")
            print("Please review the output above for specific errors from spotDL or your system.")
        else:
            print(f"\n--- Command Completed Successfully ---")

        return return_code, collected_lines
    except FileNotFoundError:
        print(f"\nError: The command '{command_parts[0]}' was not found.")
        print("Please ensure 'spotdl' and 'ffmpeg' are correctly installed and accessible in your system's PATH.")
        print("If you are using a Python virtual environment, ensure it is activated.")
        return 1, collected_lines
    except Exception as e:
        print(f"\nAn unexpected error occurred while trying to run the command: {e}")
        return 1, collected_lines

def get_user_input(prompt: str, default: Optional[str] = None) -> str:
    """
    Prompts the user for input with an optional default value.
    Returns the user's input or the default value.
    """
    if default is not None:
        return input(f"{prompt} (default: {default}): ").strip() or default
    return input(f"{prompt}: ").strip()

def get_user_choice(prompt: str, options: List[str]) -> str:
    """
    Presents a list of options to the user and returns their valid choice.
    Ensures the user selects a valid number from the list.
    """
    while True:
        print(f"\n{prompt}")
        for i, option in enumerate(options):
            print(f"  {i+1}. {option}")
        
        choice_str = get_user_input("Enter your choice (number)")
        try:
            choice_idx = int(choice_str) - 1
            if 0 <= choice_idx < len(options):
                return options[choice_idx]
            else:
                print("Invalid choice. Please enter a number corresponding to an option from the list.")
        except ValueError:
            print("Invalid input. Please enter a whole number.")

def validate_and_create_dir(path_str: str) -> Optional[Path]:
    """
    Validates a directory path string, converts it to a Path object,
    and attempts to create the directory if it doesn't exist.
    Returns a Path object on success, None on failure.
    """
    if not path_str:
        return None # Empty string for output path usually means current directory, handled by default

    try:
        # Expand user (~) and resolve to an absolute path for consistency
        path = Path(path_str).expanduser().resolve()
        
        if not path.exists():
            print(f"Output directory '{path}' does not exist. Attempting to create it...")
            path.mkdir(parents=True, exist_ok=True) # parents=True creates any necessary parent dirs
        elif not path.is_dir():
            print(f"Error: '{path}' exists but is not a directory. Please provide a valid directory path.")
            return None
        return path
    except Exception as e:
        print(f"Error validating or creating directory '{path_str}': {e}")
        return None

def get_numeric_input(prompt: str, default: Optional[int] = None, min_value: int = 0) -> Optional[int]:
    """
    Gets a numeric input from the user, validates it, and returns an integer.
    Supports default values and minimum value constraints.
    """
    while True:
        user_input = get_user_input(prompt, str(default) if default is not None else "")
        if not user_input and default is not None:
            return default
        if not user_input: # If no input and no default, return None
            return None
        try:
            value = int(user_input)
            if value >= min_value:
                return value
            else:
                print(f"Please enter a number greater than or equal to {min_value}.")
        except ValueError:
            print("Invalid input. Please enter a valid whole number.")

# --- spotDL Command Option Collectors ---

def common_download_options() -> List[str]:
    """Collects common download-related options from the user for spotDL commands."""
    options = []

    # Output directory handling with Pathlib for robustness
    current_dir = Path.cwd()
    output_dir_str = get_user_input("Enter output directory (e.g., 'downloads')", default=str(current_dir))
    output_path = validate_and_create_dir(output_dir_str)
    if output_path:
        options.extend(["--output", str(output_path)]) # Pass as string for subprocess

    # Audio format
    format_choice = get_user_choice("Select audio format", ["mp3", "m4a", "flac", "opus", "wav", "aac", "custom"])
    if format_choice == "custom":
        custom_format = get_user_input("Enter custom format (e.g., 'mp3', 'm4a')").lower()
        if custom_format:
            options.extend(["--format", custom_format])
        else:
            print("No custom format entered. Format option will be skipped.")
    else:
        options.extend(["--format", format_choice])

    # Bitrate: Corrected to use '0' for best quality as per spotDL CLI
    # Valid options from spotDL --help: {auto,disable,8k,16k,...,320k,0,1,2,...,9}
    bitrate_options = ["0", "320k", "256k", "128k", "auto", "disable", "custom"] # '0' for best quality
    bitrate_choice = get_user_choice(
        "Select audio bitrate (default: 0 - highest possible quality. 320k is a fixed bitrate)",
        bitrate_options
    )
    if bitrate_choice == "custom":
        custom_bitrate = get_user_input("Enter custom bitrate (e.g., '192k') or a quality level (0-9)").lower()
        if custom_bitrate:
            options.extend(["--bitrate", custom_bitrate])
        else:
            print("No custom bitrate entered. Bitrate option will be skipped.")
    else:
        options.extend(["--bitrate", bitrate_choice])

    # Lyrics embedding
    if get_user_input("Embed lyrics? (yes/no)", default="yes").lower() == "no":
        options.append("--no-lyrics")
    else:
        options.append("--lyrics") # Explicitly add, though it's often the default

    # Metadata embedding (album art, etc.)
    if get_user_input("Embed metadata (album art, track info, etc.)? (yes/no)", default="yes").lower() == "no":
        options.append("--no-metadata")
    
    # SponsorBlock integration
    if get_user_input("Enable SponsorBlock (requires YouTube sources)? (yes/no)", default="no").lower() == "yes":
        options.append("--sponsor-block")

    # Overwrite behavior (corrected options from spotDL documentation)
    overwrite_options = ["skip", "force", "metadata"] # 'ask' is not a valid spotDL option
    overwrite_choice = get_user_choice("How to handle existing files?", overwrite_options)
    options.extend(["--overwrite", overwrite_choice])

    # Number of concurrent download threads
    threads = get_numeric_input("Number of concurrent download threads", default=4, min_value=1)
    if threads is not None:
        options.extend(["--threads", str(threads)])

    return options

# --- Main Operations for spotDL Commands ---

def parse_failed_downloads(output_lines: List[str]) -> List[str]:
    """
    Parses spotDL output lines to identify failed song downloads.
    Returns a list of strings, each representing a failed song (e.g., "Song Name - Artist" or "URL (Error Type)").
    """
    failed_songs = set() # Use a set to avoid duplicates

    # Pattern for explicit failures with song name (existing and works for explicit skips/errors)
    explicit_failure_pattern = re.compile(
        r".*?(?:Could not find a match for:|Failed to download|Track found but download failed):\s*(.*?)(?::.*)?$"
    )
    
    # Pattern to detect AudioProviderError and the URL that follows it
    youtube_url_pattern = re.compile(r"https?://(?:www\.)?(?:music\.)?youtube\.com/watch\?v=[\w-]+")
    
    i = 0
    while i < len(output_lines):
        line = output_lines[i]
        
        # 1. Check for explicit spotDL failure messages that include song name
        explicit_match = explicit_failure_pattern.search(line)
        if explicit_match:
            song_info = explicit_match.group(1).strip()
            if song_info:
                failed_songs.add(song_info)
            i += 1
            continue

        # 2. Check for AudioProviderError and try to find an associated YouTube URL
        if "AudioProviderError:" in line:
            yt_url = None
            # Look for a URL in the current line or the next 2-3 lines
            for j in range(i, min(i + 4, len(output_lines))): 
                url_match = youtube_url_pattern.search(output_lines[j])
                if url_match:
                    yt_url = url_match.group(0)
                    break
            
            if yt_url:
                failed_songs.add(f"Download failed for YouTube URL: {yt_url} (AudioProviderError)")
            else:
                # If no specific URL found near the error, report generic error
                failed_songs.add(f"Download failed due to AudioProviderError (details in log: '{line}')")
            
            i += 1 # Move past the current error line
            continue

        i += 1 # Move to the next line if no match

    return sorted(list(failed_songs))


def download_songs():
    """Handles the 'spotdl download' operation with user interaction."""
    urls_str = get_user_input("Enter Spotify URLs (track, album, playlist, artist, separated by space or newline)")
    urls = [url.strip() for url in urls_str.split() if url.strip()] # Handles space or newline separated
    
    if not urls:
        print("No Spotify URLs provided. Aborting download.")
        return

    command_parts = ["spotdl", "download"]
    command_parts.extend(urls)
    command_parts.extend(common_download_options())

    # Special options for playlists/albums
    # Check if any provided URL hints at being a playlist or album for relevant prompts
    is_playlist_or_album = any("playlist" in url.lower() or "album" in url.lower() for url in urls)
    if is_playlist_or_album:
        playlist_start = get_numeric_input("Start index for playlist/album (leave empty for start)", default=None, min_value=1)
        if playlist_start is not None:
            command_parts.extend(["--playlist-start", str(playlist_start)])
        
        playlist_end = get_numeric_input("End index for playlist/album (leave empty for end)", default=None, min_value=1)
        if playlist_end is not None:
            command_parts.extend(["--playlist-end", str(playlist_end)])
        
        # Using --archive for the archive file in spotDL v4
        archive_file_str = get_user_input("Path to archive file to skip already downloaded songs (e.g., 'archive.txt', leave empty for none)", default="")
        if archive_file_str:
            archive_path = Path(archive_file_str).expanduser().resolve()
            command_parts.extend(["--archive", str(archive_path)])

    # Custom search query for non-Spotify URLs (or when Spotify match is poor)
    search_query = get_user_input("Optional: Custom search query for non-Spotify URLs (e.g., 'artist - title', leave empty for none)", default="")
    if search_query:
        command_parts.extend(["--search-query", search_query])

    # Advanced arguments for advanced users
    advanced_args_str = get_user_input(
        "Enter any additional spotDL arguments (e.g., --ffmpeg-args \"-vn -loglevel quiet\", --yt-dlp-args \"--no-check-certificate\"). "
        "Use quotes around values if they contain spaces. Leave empty for none.",
        default=""
    )
    if advanced_args_str:
        try:
            # shlex.split correctly handles arguments with spaces if they are quoted
            command_parts.extend(shlex.split(advanced_args_str))
        except ValueError as e:
            print(f"Warning: Could not parse advanced arguments '{advanced_args_str}'. Please check your quoting: {e}")
            print("Advanced arguments will be skipped for this command.")

    # Execute command and capture output
    return_code, collected_output_lines = run_command(command_parts)

    # Summarize failed downloads
    failed_songs = parse_failed_downloads(collected_output_lines)
    if failed_songs:
        print("\n--- Summary of Skipped/Failed Downloads ---")
        for song in failed_songs:
            print(f"- {song}")
        print("-------------------------------------------\n")
    elif return_code != 0:
        print("\nNo specific song failures detected in output, but the command failed. Please review the full log for details.")
    else:
        print("\nAll requested songs were processed successfully (or skipped according to --overwrite rules).\n")


def save_metadata():
    """Handles the 'spotdl save' operation."""
    urls_str = get_user_input("Enter Spotify URLs (track, album, playlist, artist, separated by space or newline)")
    urls = [url.strip() for url in urls_str.split() if url.strip()]
    if not urls:
        print("No Spotify URLs provided. Aborting save operation.")
        return

    save_file_str = get_user_input("Enter filename to save metadata (e.g., 'playlist_meta.spotdl'): ")
    if not save_file_str:
        print("Filename not provided. Aborting save operation.")
        return
    
    save_path = Path(save_file_str).expanduser().resolve()
    
    command_parts = ["spotdl", "save"]
    command_parts.extend(urls)
    command_parts.extend(["--save-file", str(save_path)])

    run_command(command_parts)

def sync_playlist():
    """Handles the 'spotdl sync' operation."""
    sync_source_str = get_user_input("Enter Spotify playlist URL OR path to a .spotdl file to sync: ")
    if not sync_source_str:
        print("No sync source provided. Aborting sync operation.")
        return

    # Check if the input is likely a local .spotdl file
    sync_source_path_candidate = Path(sync_source_str).expanduser().resolve()
    is_file = sync_source_path_candidate.is_file() and sync_source_path_candidate.suffix == ".spotdl"
    
    command_parts = ["spotdl", "sync", sync_source_str]
    
    if not is_file:
        save_file_str = get_user_input(
            "Enter filename to save sync state for future updates (e.g., 'my_playlist_sync.spotdl', leave empty to not save). "
            "Using this file allows quicker future syncs without re-fetching Spotify data:",
            default=""
        )
        if save_file_str:
            save_path = Path(save_file_str).expanduser().resolve()
            command_parts.extend(["--save-file", str(save_path)])
            print(f"Note: For future syncs, you can use the command 'spotdl sync {save_path}' directly.")

    # Execute sync command and capture output
    command_parts.extend(common_download_options())
    return_code, collected_output_lines = run_command(command_parts)

    # Summarize failed downloads for sync as well
    failed_songs = parse_failed_downloads(collected_output_lines)
    if failed_songs:
        print("\n--- Summary of Skipped/Failed Sync Downloads ---")
        for song in failed_songs:
            print(f"- {song}")
        print("--------------------------------------------------\n")
    elif return_code != 0:
        print("\nNo specific song failures detected in output during sync, but the command failed. Please review the full log for details.")
    else:
        print("\nSync operation completed. All new/updated songs were processed successfully.\n")


def get_direct_urls():
    """Handles the 'spotdl url' operation (to get direct download links)."""
    urls_str = get_user_input("Enter Spotify URLs (track, album, playlist, artist, separated by space or newline)")
    urls = [url.strip() for url in urls_str.split() if url.strip()]
    if not urls:
        print("No Spotify URLs provided. Aborting URL retrieval.")
        return
    
    command_parts = ["spotdl", "url"]
    command_parts.extend(urls)

    run_command(command_parts)

# --- Main Menu and Script Execution ---

def main_menu():
    """Presents the main menu and handles user choices."""
    while True:
        print("\n--- spotDL v4 User-Friendly Downloader Script ---")
        print("1. Download Songs (from Spotify URLs)")
        print("2. Save Metadata (generate .spotdl files for tracks/playlists)")
        print("3. Sync Playlist/Album (download new, remove deleted from local)")
        print("4. Get Direct Download URLs (view source URLs without downloading audio)")
        print("5. Exit")

        choice = get_user_input("Enter your choice")

        if choice == '1':
            download_songs()
        elif choice == '2':
            save_metadata()
        elif choice == '3':
            sync_playlist()
        elif choice == '4':
            get_direct_urls()
        elif choice == '5':
            print("Exiting spotDL downloader. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter a number from the menu (1-5).")

if __name__ == "__main__":
    print("Welcome to the spotDL v4 User-Friendly Downloader!")
    print("--------------------------------------------------")
    print("Initial Setup Checklist:")
    print("1. Activate your Python virtual environment. Example for Windows: `.\\spotdl_env\\Scripts\\activate`")
    print("   Example for macOS/Linux: `source spotdl_env/bin/activate`")
    print("2. Install spotDL within your activated environment: `pip install spotdl`")
    print("3. Install FFmpeg (required by spotDL for audio processing) if not already installed system-wide:")
    print("   Run `spotdl --download-ffmpeg` in your activated environment.")
    print("--------------------------------------------------")
    main_menu()
