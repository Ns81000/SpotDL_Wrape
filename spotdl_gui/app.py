import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import subprocess
import shlex
import os
import sys
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import threading

# --- Constants ---
APP_NAME = "spotDL GUI Downloader"
DEFAULT_OUTPUT_DIR = str(Path.cwd() / "spotdl_downloads")
AUDIO_FORMATS = ["mp3", "m4a", "flac", "opus", "wav", "aac", "custom"]
BITRATE_OPTIONS = ["0 (best)", "320k", "256k", "192k", "128k", "96k", "auto", "disable", "custom"]
OVERWRITE_OPTIONS = ["skip", "force", "metadata"]

class SpotDLGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("800x700") # Adjusted for better layout

        # --- Variables ---
        self.urls_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value=DEFAULT_OUTPUT_DIR)
        self.audio_format_var = tk.StringVar(value=AUDIO_FORMATS[0])
        self.custom_audio_format_var = tk.StringVar()
        self.bitrate_var = tk.StringVar(value=BITRATE_OPTIONS[0])
        self.custom_bitrate_var = tk.StringVar()
        self.embed_lyrics_var = tk.BooleanVar(value=True)
        self.embed_metadata_var = tk.BooleanVar(value=True)
        self.sponsor_block_var = tk.BooleanVar(value=False)
        self.overwrite_var = tk.StringVar(value=OVERWRITE_OPTIONS[0])
        self.threads_var = tk.IntVar(value=4)
        self.save_file_var = tk.StringVar() # For save/sync operations
        self.archive_file_var = tk.StringVar() # For download operation with archive
        self.search_query_var = tk.StringVar()
        self.advanced_args_var = tk.StringVar()

        # --- UI Setup ---
        self._create_widgets()
        self._setup_layout()
        self._check_dependencies()

    def _check_dependencies(self):
        """Checks for spotdl and ffmpeg."""
        try:
            subprocess.run(["spotdl", "--version"], capture_output=True, check=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log_message("ERROR: spotDL command not found. Please ensure spotDL is installed and in your PATH.")
            self.log_message("You can install it using: pip install spotdl")
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log_message("WARNING: FFmpeg not found. spotDL may not function correctly without it.")
            self.log_message("spotDL can try to download it for you. Run 'spotdl --download-ffmpeg' in your terminal.")


    def _create_widgets(self):
        # Main frame
        self.main_frame = ttk.Frame(self, padding="10")

        # URL Input
        self.url_label = ttk.Label(self.main_frame, text="Spotify URLs (track, album, playlist, artist - separated by space or newline):")
        self.url_entry = ttk.Entry(self.main_frame, textvariable=self.urls_var, width=80) # Increased width

        # --- Common Download Options Frame ---
        self.options_frame = ttk.LabelFrame(self.main_frame, text="Download Options", padding="10")

        # Output Directory
        self.output_dir_label = ttk.Label(self.options_frame, text="Output Directory:")
        self.output_dir_entry = ttk.Entry(self.options_frame, textvariable=self.output_dir_var, width=50)
        self.browse_output_button = ttk.Button(self.options_frame, text="Browse...", command=self._browse_output_dir)

        # Audio Format
        self.audio_format_label = ttk.Label(self.options_frame, text="Audio Format:")
        self.audio_format_menu = ttk.OptionMenu(self.options_frame, self.audio_format_var, self.audio_format_var.get(), *AUDIO_FORMATS, command=self._toggle_custom_format_entry)
        self.custom_audio_format_entry = ttk.Entry(self.options_frame, textvariable=self.custom_audio_format_var, width=10, state=tk.DISABLED)

        # Bitrate
        self.bitrate_label = ttk.Label(self.options_frame, text="Bitrate:")
        self.bitrate_menu = ttk.OptionMenu(self.options_frame, self.bitrate_var, self.bitrate_var.get(), *BITRATE_OPTIONS, command=self._toggle_custom_bitrate_entry)
        self.custom_bitrate_entry = ttk.Entry(self.options_frame, textvariable=self.custom_bitrate_var, width=10, state=tk.DISABLED)

        # Threads
        self.threads_label = ttk.Label(self.options_frame, text="Download Threads:")
        self.threads_spinbox = ttk.Spinbox(self.options_frame, from_=1, to_=32, textvariable=self.threads_var, width=5)

        # Checkboxes
        self.embed_lyrics_check = ttk.Checkbutton(self.options_frame, text="Embed Lyrics", variable=self.embed_lyrics_var)
        self.embed_metadata_check = ttk.Checkbutton(self.options_frame, text="Embed Metadata (Art, Info)", variable=self.embed_metadata_var)
        self.sponsor_block_check = ttk.Checkbutton(self.options_frame, text="Enable SponsorBlock (YouTube)", variable=self.sponsor_block_var)

        # Overwrite
        self.overwrite_label = ttk.Label(self.options_frame, text="Overwrite Existing Files:")
        self.overwrite_menu = ttk.OptionMenu(self.options_frame, self.overwrite_var, self.overwrite_var.get(), *OVERWRITE_OPTIONS)

        # --- Advanced/Specific Options Frame ---
        self.advanced_options_frame = ttk.LabelFrame(self.main_frame, text="Advanced/Specific Options", padding="10")

        # Save File (for metadata save/sync)
        self.save_file_label = ttk.Label(self.advanced_options_frame, text="Save/Sync State File (.spotdl):")
        self.save_file_entry = ttk.Entry(self.advanced_options_frame, textvariable=self.save_file_var, width=40)
        self.browse_save_file_button = ttk.Button(self.advanced_options_frame, text="Browse...", command=self._browse_save_file)

        # Archive File (for download)
        self.archive_file_label = ttk.Label(self.advanced_options_frame, text="Archive File (skip downloaded):")
        self.archive_file_entry = ttk.Entry(self.advanced_options_frame, textvariable=self.archive_file_var, width=40)
        self.browse_archive_file_button = ttk.Button(self.advanced_options_frame, text="Browse...", command=self._browse_archive_file)

        # Search Query
        self.search_query_label = ttk.Label(self.advanced_options_frame, text="Custom Search Query (optional):")
        self.search_query_entry = ttk.Entry(self.advanced_options_frame, textvariable=self.search_query_var, width=50)

        # Additional spotDL Arguments
        self.advanced_args_label = ttk.Label(self.advanced_options_frame, text="Additional spotDL Arguments:")
        self.advanced_args_entry = ttk.Entry(self.advanced_options_frame, textvariable=self.advanced_args_var, width=50)


        # --- Action Buttons Frame ---
        self.actions_frame = ttk.Frame(self.main_frame, padding="10")
        self.download_button = ttk.Button(self.actions_frame, text="Download Songs", command=self._download_songs)
        self.save_meta_button = ttk.Button(self.actions_frame, text="Save Metadata", command=self._save_metadata)
        self.sync_button = ttk.Button(self.actions_frame, text="Sync Playlist/Album", command=self._sync_playlist)
        self.get_urls_button = ttk.Button(self.actions_frame, text="Get Direct URLs", command=self._get_direct_urls)
        self.clear_log_button = ttk.Button(self.actions_frame, text="Clear Log", command=self._clear_log)


        # Output Console
        self.output_console_label = ttk.Label(self.main_frame, text="Output Log:")
        self.output_console = scrolledtext.ScrolledText(self.main_frame, height=15, width=90, wrap=tk.WORD, state=tk.DISABLED)

        # Status Bar (Placeholder)
        self.status_bar = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)

    def _setup_layout(self):
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # URL Input
        self.url_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=(0,2))
        self.url_entry.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=(0,10))

        # Common Download Options
        self.options_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.options_frame.columnconfigure(1, weight=1) # Make entry fields expand

        self.output_dir_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.output_dir_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.browse_output_button.grid(row=0, column=2, sticky="e", padx=5, pady=2)

        self.audio_format_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.audio_format_menu.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        self.custom_audio_format_entry.grid(row=1, column=2, sticky="w", padx=5, pady=2) # Next to menu

        self.bitrate_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.bitrate_menu.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        self.custom_bitrate_entry.grid(row=2, column=2, sticky="w", padx=5, pady=2) # Next to menu

        self.threads_label.grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.threads_spinbox.grid(row=3, column=1, sticky="w", padx=5, pady=2)

        self.overwrite_label.grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.overwrite_menu.grid(row=4, column=1, sticky="w", padx=5, pady=2)

        # Checkboxes in a sub-frame for better grouping if needed, or directly
        checkbox_frame = ttk.Frame(self.options_frame)
        checkbox_frame.grid(row=5, column=0, columnspan=3, sticky="w", pady=5)
        self.embed_lyrics_check.pack(side=tk.LEFT, padx=5)
        self.embed_metadata_check.pack(side=tk.LEFT, padx=5)
        self.sponsor_block_check.pack(side=tk.LEFT, padx=5)

        # Advanced/Specific Options
        self.advanced_options_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.advanced_options_frame.columnconfigure(1, weight=1)

        self.save_file_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.save_file_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.browse_save_file_button.grid(row=0, column=2, sticky="e", padx=5, pady=2)

        self.archive_file_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.archive_file_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.browse_archive_file_button.grid(row=1, column=2, sticky="e", padx=5, pady=2)

        self.search_query_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.search_query_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5, pady=2)

        self.advanced_args_label.grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.advanced_args_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=2)

        # Action Buttons
        self.actions_frame.grid(row=4, column=0, columnspan=3, pady=10)
        self.download_button.pack(side=tk.LEFT, padx=5)
        self.save_meta_button.pack(side=tk.LEFT, padx=5)
        self.sync_button.pack(side=tk.LEFT, padx=5)
        self.get_urls_button.pack(side=tk.LEFT, padx=5)
        self.clear_log_button.pack(side=tk.LEFT, padx=5)


        # Output Console
        self.output_console_label.grid(row=5, column=0, columnspan=3, sticky="w", padx=5, pady=(5,0))
        self.output_console.grid(row=6, column=0, columnspan=3, sticky="nsew", padx=5, pady=(0,5))
        self.main_frame.rowconfigure(6, weight=1) # Make console expand vertically
        self.main_frame.columnconfigure(0, weight=1) # Make console expand horizontally (via columnspan)


        # Status Bar
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _toggle_custom_format_entry(self, choice):
        if choice == "custom":
            self.custom_audio_format_entry.config(state=tk.NORMAL)
        else:
            self.custom_audio_format_entry.config(state=tk.DISABLED)
            self.custom_audio_format_var.set("")

    def _toggle_custom_bitrate_entry(self, choice):
        if choice == "custom":
            self.custom_bitrate_entry.config(state=tk.NORMAL)
        else:
            self.custom_bitrate_entry.config(state=tk.DISABLED)
            self.custom_bitrate_var.set("")

    def _browse_output_dir(self):
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get() or Path.home())
        if directory:
            self.output_dir_var.set(directory)

    def _browse_save_file(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".spotdl",
            filetypes=[("spotDL files", "*.spotdl"), ("All files", "*.*")],
            initialdir=Path.home(),
            title="Select Save/Sync State File"
        )
        if filepath:
            self.save_file_var.set(filepath)

    def _browse_archive_file(self):
        filepath = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=Path.home(),
            title="Select Archive File"
        )
        if filepath:
            self.archive_file_var.set(filepath)

    def log_message(self, message: str, clear_first: bool = False):
        self.output_console.config(state=tk.NORMAL)
        if clear_first:
            self.output_console.delete(1.0, tk.END)
        self.output_console.insert(tk.END, message + "\n")
        self.output_console.see(tk.END) # Scroll to the end
        self.output_console.config(state=tk.DISABLED)
        self.update_idletasks() # Ensure GUI updates

    def _clear_log(self):
        self.output_console.config(state=tk.NORMAL)
        self.output_console.delete(1.0, tk.END)
        self.output_console.config(state=tk.DISABLED)
        self.status_bar.config(text="Log cleared.")

    def _set_status(self, message: str):
        self.status_bar.config(text=message)
        self.update_idletasks()

    def _get_urls_from_input(self) -> List[str]:
        urls_text = self.urls_var.get()
        if not urls_text:
            self.log_message("Error: No Spotify URLs provided.")
            return []
        # Split by space or newline, remove empty strings
        return [url.strip() for url in re.split(r'[ \n]+', urls_text) if url.strip()]

    def _validate_and_create_dir(self, path_str: str) -> Optional[Path]:
        if not path_str: # Should not happen if default is set, but good practice
            self.log_message("Error: Output directory is empty.")
            return None
        try:
            path = Path(path_str).expanduser().resolve()
            if not path.exists():
                self.log_message(f"Output directory '{path}' does not exist. Creating it...")
                path.mkdir(parents=True, exist_ok=True)
            elif not path.is_dir():
                self.log_message(f"Error: '{path}' exists but is not a directory.")
                return None
            return path
        except Exception as e:
            self.log_message(f"Error creating/validating directory '{path_str}': {e}")
            return None

    def _build_common_download_options(self) -> List[str]:
        options = []
        output_dir = self.output_dir_var.get()
        validated_output_path = self._validate_and_create_dir(output_dir)
        if validated_output_path:
            options.extend(["--output", str(validated_output_path)])
        else:
            # If validation failed, an error message is already logged.
            # We might want to prevent command execution here or let spotDL handle it.
            # For now, proceed, spotDL will likely use current dir or error out.
            self.log_message("Warning: Output directory is invalid. spotDL might use current directory or fail.")


        # Audio Format
        audio_format = self.audio_format_var.get()
        if audio_format == "custom":
            custom_format = self.custom_audio_format_var.get().strip().lower()
            if custom_format:
                options.extend(["--format", custom_format])
            else:
                self.log_message("Custom audio format selected but not specified. Skipping format option.")
        else:
            options.extend(["--format", audio_format])

        # Bitrate
        bitrate = self.bitrate_var.get()
        if bitrate == "custom":
            custom_bitrate = self.custom_bitrate_var.get().strip().lower()
            if custom_bitrate:
                options.extend(["--bitrate", custom_bitrate])
            else:
                self.log_message("Custom bitrate selected but not specified. Skipping bitrate option.")
        elif bitrate == "0 (best)": # Map UI "0 (best)" to spotDL "0"
            options.extend(["--bitrate", "0"])
        else:
            options.extend(["--bitrate", bitrate])

        # Lyrics
        if not self.embed_lyrics_var.get():
            options.append("--no-lyrics")
        else: # spotDL v4 seems to default to lyrics, but being explicit can be good
            options.append("--lyrics")

        # Metadata
        if not self.embed_metadata_var.get():
            options.append("--no-metadata")
        # else: spotDL defaults to embedding metadata

        # SponsorBlock
        if self.sponsor_block_var.get():
            options.append("--sponsor-block")

        # Overwrite
        options.extend(["--overwrite", self.overwrite_var.get()])

        # Threads
        threads = self.threads_var.get()
        if threads > 0:
            options.extend(["--threads", str(threads)])

        return options

    def _parse_failed_downloads(self, output_lines: List[str]) -> List[str]:
        """
        Parses spotDL output lines to identify failed song downloads.
        (Copied and adapted from the original script)
        """
        failed_songs = set()
        explicit_failure_pattern = re.compile(
            r".*?(?:Could not find a match for:|Failed to download|Track found but download failed):\s*(.*?)(?::.*)?$"
        )
        youtube_url_pattern = re.compile(r"https?://(?:www\.)?(?:music\.)?youtube\.com/watch\?v=[\w-]+")

        i = 0
        while i < len(output_lines):
            line = output_lines[i]
            explicit_match = explicit_failure_pattern.search(line)
            if explicit_match:
                song_info = explicit_match.group(1).strip()
                if song_info: failed_songs.add(song_info)
                i += 1
                continue

            if "AudioProviderError:" in line:
                yt_url = None
                for j in range(i, min(i + 4, len(output_lines))):
                    url_match = youtube_url_pattern.search(output_lines[j])
                    if url_match:
                        yt_url = url_match.group(0)
                        break
                if yt_url:
                    failed_songs.add(f"Download failed for YouTube URL: {yt_url} (AudioProviderError)")
                else:
                    failed_songs.add(f"Download failed due to AudioProviderError (details in log: '{line}')")
                i += 1
                continue
            i += 1
        return sorted(list(failed_songs))

    def _run_spotdl_command(self, command_parts: List[str], operation_name: str):
        if not command_parts: # Should not happen if called correctly
            self.log_message(f"Error: No command to run for {operation_name}.")
            return

        self.log_message(f"--- Starting {operation_name} ---", clear_first=True)
        self._set_status(f"{operation_name} in progress...")
        self.log_message(f"Executing: spotdl {' '.join(shlex.quote(arg) for arg in command_parts if arg != 'spotdl')}")

        # Disable buttons during operation
        self._toggle_buttons_state(tk.DISABLED)

        collected_lines = []

        def target():
            try:
                # Ensure PATH is correctly inherited, especially if running in a virtual env
                env = os.environ.copy()

                # For Windows, prevent console window from popping up for spotdl/ffmpeg
                creationflags = 0
                if sys.platform == "win32":
                    creationflags = subprocess.CREATE_NO_WINDOW

                process = subprocess.Popen(
                    command_parts,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env,
                    creationflags=creationflags
                )

                for line in iter(process.stdout.readline, ''):
                    stripped_line = line.strip()
                    self.log_message(stripped_line) # Log to GUI
                    collected_lines.append(stripped_line)

                process.stdout.close()
                return_code = process.wait()

                if return_code != 0:
                    self.log_message(f"\n--- {operation_name} Failed with Exit Code {return_code} ---")
                    self._set_status(f"{operation_name} Failed.")
                else:
                    self.log_message(f"\n--- {operation_name} Completed Successfully ---")
                    self._set_status(f"{operation_name} Completed.")

                # Parse and display failures for download/sync operations
                if operation_name in ["Download", "Sync"]:
                    failed_songs = self._parse_failed_downloads(collected_lines)
                    if failed_songs:
                        self.log_message("\n--- Summary of Skipped/Failed Downloads ---")
                        for song in failed_songs:
                            self.log_message(f"- {song}")
                        self.log_message("-------------------------------------------\n")
                    elif return_code != 0:
                         self.log_message("\nNo specific song failures detected, but the command failed. Review log.")
                    else:
                        self.log_message("\nAll songs processed successfully or skipped as per rules.\n")

            except FileNotFoundError:
                self.log_message(f"\nError: The command '{command_parts[0]}' was not found.")
                self.log_message("Ensure 'spotdl' (and 'ffmpeg') are installed and in your system's PATH.")
                self._set_status(f"Error: {command_parts[0]} not found.")
            except Exception as e:
                self.log_message(f"\nAn unexpected error occurred: {e}")
                self._set_status(f"Unexpected error during {operation_name}.")
            finally:
                # Re-enable buttons on the main thread
                self.after(0, self._toggle_buttons_state, tk.NORMAL)

        # Run the command in a separate thread to keep GUI responsive
        thread = threading.Thread(target=target)
        thread.daemon = True # Allows main program to exit even if thread is running
        thread.start()

    def _toggle_buttons_state(self, state: str):
        """tk.NORMAL or tk.DISABLED"""
        self.download_button.config(state=state)
        self.save_meta_button.config(state=state)
        self.sync_button.config(state=state)
        self.get_urls_button.config(state=state)
        # Keep clear log button always enabled, or disable it too:
        # self.clear_log_button.config(state=state)


    def _get_advanced_args(self) -> List[str]:
        advanced_args_str = self.advanced_args_var.get().strip()
        if advanced_args_str:
            try:
                return shlex.split(advanced_args_str)
            except ValueError as e:
                self.log_message(f"Warning: Could not parse advanced arguments '{advanced_args_str}'. Check quoting: {e}")
                return []
        return []

    # --- Action Methods ---
    def _download_songs(self):
        urls = self._get_urls_from_input()
        if not urls:
            return

        command = ["spotdl", "download"]
        command.extend(urls)
        command.extend(self._build_common_download_options())

        # Archive file
        archive_file = self.archive_file_var.get().strip()
        if archive_file:
            # Validate path? For now, pass it directly.
            # spotDL will handle if it's invalid.
            command.extend(["--archive", archive_file])

        # Search query
        search_query = self.search_query_var.get().strip()
        if search_query:
            command.extend(["--search-query", search_query])

        # Advanced args
        command.extend(self._get_advanced_args())

        self._run_spotdl_command(command, "Download")

    def _save_metadata(self):
        urls = self._get_urls_from_input()
        if not urls:
            return

        save_file = self.save_file_var.get().strip()
        if not save_file:
            self.log_message("Error: 'Save/Sync State File' must be specified for saving metadata.")
            self._set_status("Save metadata error: No save file specified.")
            return

        # Basic validation for .spotdl extension
        if not save_file.endswith(".spotdl"):
            save_file += ".spotdl"
            self.log_message(f"Info: Appended '.spotdl' to save file name: {save_file}")
            self.save_file_var.set(save_file) # Update GUI

        command = ["spotdl", "save"]
        command.extend(urls)
        command.extend(["--save-file", save_file])

        # Advanced args (though less common for 'save')
        command.extend(self._get_advanced_args())

        self._run_spotdl_command(command, "Save Metadata")

    def _sync_playlist(self):
        sync_source = self.urls_var.get().strip() # Sync uses the URL field for source URL or .spotdl file
        if not sync_source:
            self.log_message("Error: No Spotify URL or .spotdl file path provided in the URL field for sync.")
            self._set_status("Sync error: No source specified.")
            return

        # Determine if it's a .spotdl file or a URL
        # Simple check, spotDL will ultimately validate
        is_spotdl_file = sync_source.lower().endswith(".spotdl") and Path(sync_source).exists()

        command = ["spotdl", "sync", sync_source]
        command.extend(self._build_common_download_options()) # Sync also downloads

        # Save file for sync state (if source is a URL)
        # If source is already a .spotdl file, spotDL updates it in place.
        if not is_spotdl_file:
            save_file = self.save_file_var.get().strip()
            if save_file:
                if not save_file.endswith(".spotdl"):
                    save_file += ".spotdl"
                    self.log_message(f"Info: Appended '.spotdl' to sync state file: {save_file}")
                    self.save_file_var.set(save_file)
                command.extend(["--save-file", save_file])
            else:
                self.log_message("Info: No 'Save/Sync State File' provided for URL sync. Sync state won't be saved to a separate file.")

        # Advanced args
        command.extend(self._get_advanced_args())

        self._run_spotdl_command(command, "Sync")

    def _get_direct_urls(self):
        urls = self._get_urls_from_input()
        if not urls:
            return

        command = ["spotdl", "url"]
        command.extend(urls)

        # Advanced args (though less common for 'url')
        command.extend(self._get_advanced_args())

        self._run_spotdl_command(command, "Get Direct URLs")


if __name__ == "__main__":
    app = SpotDLGUI()
    app.mainloop()
