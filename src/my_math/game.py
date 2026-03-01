"""Main game module for MyMath - A math learning game for children."""

import os
import random
import sys
import tkinter as tk
from importlib.metadata import version as pkg_version
from pathlib import Path
from tkinter import font as tkfont
from typing import Callable

from PIL import Image, ImageTk

from .config import get_config, Config

# Try to import VLC
try:
    import vlc

    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False


class VideoPlayer:
    """Video player using VLC for tkinter embedding."""

    _vlc_instance = None  # Shared VLC instance (expensive to create)

    @classmethod
    def warmup(cls) -> None:
        """Pre-initialize the VLC instance so first playback is instant."""
        if VLC_AVAILABLE and cls._vlc_instance is None:
            try:
                cls._vlc_instance = vlc.Instance()
            except Exception:
                cls._vlc_instance = None

    def __init__(self, parent: tk.Widget, config: Config):
        self.parent = parent
        self.config = config
        self.instance = None
        self.player = None
        self.video_frame = None
        self._available_videos: list[Path] = []

        if VLC_AVAILABLE:
            try:
                # Reuse the shared VLC instance
                if VideoPlayer._vlc_instance is None:
                    VideoPlayer._vlc_instance = vlc.Instance()
                self.instance = VideoPlayer._vlc_instance
                self.player = self.instance.media_player_new()
            except Exception:
                self.instance = None
                self.player = None

    def _load_available_videos(self) -> None:
        """Load list of available videos from the videos folder."""
        videos_folder = self.config.videos_folder
        self._available_videos = []

        if videos_folder.exists():
            for ext in ["*.mp4", "*.avi", "*.mkv", "*.mov", "*.wmv", "*.webm"]:
                self._available_videos.extend(videos_folder.glob(ext))

    def get_random_video(self) -> Path | None:
        """Get a random video from the videos folder."""
        self._load_available_videos()
        if self._available_videos:
            return random.choice(self._available_videos)
        return None

    def create_frame(self, parent: tk.Widget) -> tk.Frame:
        """Create and return a frame for video embedding."""
        self.video_frame = tk.Frame(parent, bg="black")
        return self.video_frame

    def play(self, video_path: Path) -> bool:
        """Play a video file."""
        if not VLC_AVAILABLE or self.player is None or self.video_frame is None:
            return False

        try:
            media = self.instance.media_new(str(video_path))
            self.player.set_media(media)

            # Get the window handle for embedding
            if sys.platform == "win32":
                self.player.set_hwnd(self.video_frame.winfo_id())
            elif sys.platform == "darwin":
                self.player.set_nsobject(self.video_frame.winfo_id())
            else:
                self.player.set_xwindow(self.video_frame.winfo_id())

            self.player.play()
            return True
        except Exception as e:
            print(f"Error playing video: {e}")
            return False

    def stop(self) -> None:
        """Stop the video playback."""
        if self.player is not None:
            try:
                self.player.stop()
            except Exception:
                pass

    def is_available(self) -> bool:
        """Check if video playback is available."""
        return VLC_AVAILABLE and self.player is not None


class SoundPlayer:
    """Simple sound player using platform-specific methods."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._winsound_available = False

        if enabled:
            try:
                import winsound

                self._winsound_available = True
            except ImportError:
                pass

    def play(self, sound_path: Path) -> None:
        """Play a sound file."""
        if not self.enabled or not sound_path.exists():
            return

        try:
            if self._winsound_available:
                import winsound

                winsound.PlaySound(
                    str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC
                )
        except Exception:
            pass  # Silently fail if sound can't be played

    def play_random_from_folder(self, folder_path: Path) -> None:
        """Play a random sound file from a folder."""
        if not self.enabled or not folder_path.exists():
            return

        # Find all sound files in the folder
        sound_files = []
        for ext in ["*.wav", "*.mp3", "*.ogg"]:
            sound_files.extend(folder_path.glob(ext))

        if sound_files:
            sound_path = random.choice(sound_files)
            self.play(sound_path)


class BaseView(tk.Frame):
    """Base class for all game views."""

    def __init__(self, parent: tk.Widget, controller: "GameController"):
        super().__init__(parent)
        self.controller = controller
        self.config = controller.config
        self.configure(bg="#f0f0f0")

    def show(self) -> None:
        """Called when this view is shown."""
        pass

    def hide(self) -> None:
        """Called when this view is hidden."""
        pass


class MainMenuView(BaseView):
    """Main menu view with game mode selection."""

    def __init__(self, parent: tk.Widget, controller: "GameController"):
        super().__init__(parent, controller)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the main menu UI."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header frame with icon and title side by side
        header_frame = tk.Frame(self, bg="#f0f0f0")
        header_frame.grid(row=0, column=0, pady=(50, 30))

        # Icon image
        self.icon_image = None
        icon_path = self.config.get_path("icon_image")
        if icon_path.exists():
            try:
                img = Image.open(icon_path)
                img = img.resize((150, 150), Image.Resampling.LANCZOS)
                self.icon_image = ImageTk.PhotoImage(img)
                icon_label = tk.Label(header_frame, image=self.icon_image, bg="#f0f0f0")
                icon_label.pack(side="left", padx=(0, 20))
            except Exception:
                pass

        # Title
        title_font = tkfont.Font(family="Arial", size=48, weight="bold")
        self.title_label = tk.Label(
            header_frame,
            text=self.config.title,
            font=title_font,
            bg="#f0f0f0",
            fg="#2c3e50",
        )
        self.title_label.pack(side="left")

        # Button frame
        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.grid(row=1, column=0, pady=20)

        # Button style
        button_color = self.config.game_button_color
        # Calculate darker shade for active state
        button_font = tkfont.Font(family="Arial", size=24, weight="bold")
        button_config = {
            "font": button_font,
            "width": 15,
            "height": 2,
            "relief": "flat",
            "cursor": "hand2",
            "bg": button_color,
            "fg": "white",
            "activebackground": button_color,
            "activeforeground": "white",
        }

        # Counting game button
        self.counting_btn = tk.Button(
            button_frame,
            text="🔢  1 2 3",
            command=lambda: self.controller.show_view("counting"),
            **button_config,
        )
        self.counting_btn.pack(pady=15)

        # Addition game button
        self.game2_btn = tk.Button(
            button_frame,
            text="➕",
            command=lambda: self.controller.show_view("addition"),
            **button_config,
        )
        self.game2_btn.pack(pady=15)

        # Settings button
        self.settings_btn = tk.Button(
            button_frame,
            text="⚙️ Settings",
            font=button_font,
            width=15,
            height=2,
            relief="flat",
            cursor="hand2",
            bg="#9b59b6",
            fg="white",
            activebackground="#8e44ad",
            activeforeground="white",
            command=lambda: self.controller.show_view("settings"),
        )
        self.settings_btn.pack(pady=15)

        # Exit button
        self.exit_btn = tk.Button(
            button_frame,
            text="🚪",
            font=button_font,
            width=15,
            height=2,
            relief="flat",
            cursor="hand2",
            bg="#e67e22",
            fg="white",
            activebackground="#d35400",
            activeforeground="white",
            command=self.controller.quit_game,
        )
        self.exit_btn.pack(pady=15)

        # Version label at the bottom center
        try:
            ver = pkg_version("my_math")
        except Exception:
            ver = "?"
        version_font = tkfont.Font(family="Arial", size=9)
        version_label = tk.Label(
            self,
            text=f"v{ver}",
            font=version_font,
            bg="#f0f0f0",
            fg="#aaaaaa",
        )
        version_label.grid(row=2, column=0, pady=(0, 10), sticky="s")

    def show(self) -> None:
        """Update title when shown (in case config changed)."""
        self.title_label.config(text=self.config.title)


class SettingsView(BaseView):
    """Settings view for editing configuration."""

    def __init__(self, parent: tk.Widget, controller: "GameController"):
        super().__init__(parent, controller)
        self.entries: dict[str, tk.Widget] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the settings UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header with back button
        header = tk.Frame(self, bg="#f0f0f0")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        header.grid_columnconfigure(1, weight=1)

        back_font = tkfont.Font(family="Arial", size=14)
        self.back_btn = tk.Button(
            header,
            text="⬅️",
            font=back_font,
            bg="#95a5a6",
            fg="white",
            relief="flat",
            cursor="hand2",
            command=lambda: self.controller.show_view("main_menu"),
        )
        self.back_btn.grid(row=0, column=0, sticky="w")

        title_font = tkfont.Font(family="Arial", size=24, weight="bold")
        title_label = tk.Label(
            header,
            text="⚙️ Settings",
            font=title_font,
            bg="#f0f0f0",
            fg="#2c3e50",
        )
        title_label.grid(row=0, column=1)

        # Save button
        save_btn = tk.Button(
            header,
            text="💾 Save",
            font=back_font,
            bg="#27ae60",
            fg="white",
            relief="flat",
            cursor="hand2",
            command=self._save_settings,
        )
        save_btn.grid(row=0, column=2, sticky="e")

        # Scrollable frame for settings
        canvas_frame = tk.Frame(self, bg="#f0f0f0")
        canvas_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_frame, bg="#f0f0f0", highlightthickness=0)
        scrollbar = tk.Scrollbar(
            canvas_frame, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f0f0f0")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Bind mouse wheel for scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Bind canvas resize to update scrollable frame width
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Build settings fields
        self._build_settings_fields()

    def _on_canvas_configure(self, event: tk.Event) -> None:
        """Update scrollable frame width when canvas is resized."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _build_settings_fields(self) -> None:
        """Build the settings input fields based on config structure."""
        # Define the settings fields with their types and descriptions
        settings_schema = [
            ("title", "str", "Game Title", "The title displayed in the window"),
            ("icon_image", "str", "Icon Image", "Path to the icon image file"),
            (
                "images_folder",
                "str",
                "Images Folder",
                "Path to folder containing game images",
            ),
            ("sound.enabled", "bool", "Sound Enabled", "Enable or disable sounds"),
            (
                "sound.correct_sound",
                "str",
                "Sounds Folder",
                "Path to folder containing sound files",
            ),
            (
                "video.videos_folder",
                "str",
                "Videos Folder",
                "Path to folder containing reward videos",
            ),
            (
                "video.min_rounds",
                "int",
                "Min Rounds for Video",
                "Minimum rounds needed to unlock video reward",
            ),
            (
                "video.max_wrong",
                "int",
                "Max Wrong for Video",
                "Maximum wrong answers allowed for video reward",
            ),
            (
                "window.fullscreen",
                "bool",
                "Fullscreen Mode",
                "Start the game in fullscreen mode",
            ),
            (
                "game.max_number",
                "int",
                "Max Number",
                "Maximum number for counting/addition games",
            ),
            (
                "game.rounds",
                "int",
                "Rounds per Game",
                "Number of rounds in each game session",
            ),
            (
                "game.image_size",
                "int",
                "Image Size (px)",
                "Maximum size of images in pixels",
            ),
            (
                "game.delay_ms",
                "int",
                "Delay (ms)",
                "Delay between steps in milliseconds",
            ),
            (
                "game.group_gap",
                "int",
                "Group Gap (px)",
                "Gap between groups of 5 images",
            ),
            (
                "game.button_color",
                "str",
                "Button Color",
                "Color for game mode buttons (hex code)",
            ),
        ]

        label_font = tkfont.Font(family="Arial", size=12, weight="bold")
        desc_font = tkfont.Font(family="Arial", size=10)
        entry_font = tkfont.Font(family="Arial", size=12)

        for i, (key, field_type, label, description) in enumerate(settings_schema):
            # Container for each setting
            row_frame = tk.Frame(
                self.scrollable_frame, bg="#ffffff", relief="groove", bd=1
            )
            row_frame.grid(row=i, column=0, sticky="ew", padx=10, pady=5)
            row_frame.grid_columnconfigure(1, weight=1)
            self.scrollable_frame.grid_columnconfigure(0, weight=1)

            # Label
            lbl = tk.Label(
                row_frame,
                text=label,
                font=label_font,
                bg="#ffffff",
                fg="#2c3e50",
                anchor="w",
            )
            lbl.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

            # Description
            desc_lbl = tk.Label(
                row_frame,
                text=description,
                font=desc_font,
                bg="#ffffff",
                fg="#7f8c8d",
                anchor="w",
            )
            desc_lbl.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))

            # Input field
            current_value = self.config.get(key, "")

            if field_type == "bool":
                var = tk.BooleanVar(value=bool(current_value))
                widget = tk.Checkbutton(
                    row_frame,
                    variable=var,
                    bg="#ffffff",
                    activebackground="#ffffff",
                    font=entry_font,
                )
                widget.var = var  # Store reference to variable
                widget.grid(row=0, column=1, rowspan=2, sticky="e", padx=10, pady=10)
            else:
                widget = tk.Entry(row_frame, font=entry_font, width=40)
                widget.insert(
                    0, str(current_value) if current_value is not None else ""
                )
                widget.grid(row=0, column=1, rowspan=2, sticky="e", padx=10, pady=10)

            self.entries[key] = (widget, field_type)

    def _save_settings(self) -> None:
        """Save the settings to config.yaml."""
        for key, (widget, field_type) in self.entries.items():
            if field_type == "bool":
                value = widget.var.get()
            elif field_type == "int":
                try:
                    value = int(widget.get())
                except ValueError:
                    value = 0
            else:
                value = widget.get()

            self.config.set(key, value)

        self.config.save()

        # Show save confirmation
        self._show_save_confirmation()

    def _show_save_confirmation(self) -> None:
        """Show a brief confirmation that settings were saved."""
        confirm_label = tk.Label(
            self,
            text="✓ Settings saved!",
            font=tkfont.Font(family="Arial", size=14, weight="bold"),
            bg="#27ae60",
            fg="white",
            padx=20,
            pady=10,
        )
        confirm_label.place(relx=0.5, rely=0.9, anchor="center")
        self.after(2000, confirm_label.destroy)

    def show(self) -> None:
        """Refresh settings values when view is shown."""
        # Update all entry fields with current config values
        for key, (widget, field_type) in self.entries.items():
            current_value = self.config.get(key, "")
            if field_type == "bool":
                widget.var.set(bool(current_value))
            else:
                widget.delete(0, tk.END)
                widget.insert(
                    0, str(current_value) if current_value is not None else ""
                )

    def hide(self) -> None:
        """Unbind mousewheel when hiding."""
        pass


class CountingGameView(BaseView):
    """Counting game view where children count images."""

    def __init__(self, parent: tk.Widget, controller: "GameController"):
        super().__init__(parent, controller)
        self.current_round = 0
        self.correct_answer = 0
        self.history: list[dict] = []  # Track game history
        self.images: list[ImageTk.PhotoImage] = []  # Keep references
        self.answer_buttons: list[tk.Button] = []
        self.available_images: list[Path] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the counting game UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=3)  # Image area (2/3 of remaining)
        self.grid_rowconfigure(2, weight=0)  # Answer area (fixed height)

        # Header with back button and round info
        header = tk.Frame(self, bg="#f0f0f0")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        header.grid_columnconfigure(1, weight=1)

        back_font = tkfont.Font(family="Arial", size=14)
        self.back_btn = tk.Button(
            header,
            text="⬅️",
            font=back_font,
            bg="#95a5a6",
            fg="white",
            relief="flat",
            cursor="hand2",
            command=lambda: self.controller.show_view("main_menu"),
        )
        self.back_btn.grid(row=0, column=0, sticky="w")

        # Progress boxes frame
        self.progress_frame = tk.Frame(header, bg="#f0f0f0")
        self.progress_frame.grid(row=0, column=1)
        self.progress_boxes: list[tk.Canvas] = []

        # Image display area
        self.image_frame = tk.Frame(self, bg="#ecf0f1")
        self.image_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.image_frame.grid_rowconfigure(0, weight=1)
        self.image_frame.grid_columnconfigure(0, weight=1)

        # Answer buttons area (centered)
        self.answer_frame = tk.Frame(self, bg="#f0f0f0")
        self.answer_frame.grid(row=2, column=0, pady=(10, 30))

    def _load_available_images(self) -> None:
        """Load list of available images from the images folder."""
        images_folder = self.config.images_folder
        self.available_images = []

        if images_folder.exists():
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp"]:
                self.available_images.extend(images_folder.glob(ext))

    def show(self) -> None:
        """Start a new counting game."""
        self._load_available_images()
        self.current_round = 0
        self.history = []
        self._init_progress_boxes()
        self._next_round()

    def _init_progress_boxes(self) -> None:
        """Initialize the progress boxes."""
        # Clear existing boxes
        for box in self.progress_boxes:
            box.destroy()
        self.progress_boxes.clear()

        # Create new boxes
        total_rounds = self.config.game_rounds
        box_size = 20
        for i in range(total_rounds):
            box = tk.Canvas(
                self.progress_frame,
                width=box_size,
                height=box_size,
                bg="#f0f0f0",
                highlightthickness=0,
            )
            box.create_rectangle(
                2,
                2,
                box_size - 2,
                box_size - 2,
                fill="#bdc3c7",  # Gray
                outline="#95a5a6",
                tags="box",
            )
            box.grid(row=0, column=i, padx=2)
            self.progress_boxes.append(box)

    def _update_progress_box(self, round_num: int, is_correct: bool) -> None:
        """Update a progress box color based on answer correctness."""
        if 0 < round_num <= len(self.progress_boxes):
            box = self.progress_boxes[round_num - 1]
            color = "#2ecc71" if is_correct else "#e74c3c"  # Green or Red
            box.delete("box")
            box_size = 20
            box.create_rectangle(
                2,
                2,
                box_size - 2,
                box_size - 2,
                fill=color,
                outline="#27ae60" if is_correct else "#c0392b",
                tags="box",
            )

    def _next_round(self) -> None:
        """Set up the next round."""
        self.current_round += 1
        total_rounds = self.config.game_rounds

        if self.current_round > total_rounds:
            self._show_results()
            return

        # Clear previous images
        for widget in self.image_frame.winfo_children():
            widget.destroy()
        self.images.clear()

        # Clear previous answer buttons
        for widget in self.answer_frame.winfo_children():
            widget.destroy()
        self.answer_buttons.clear()

        # Generate random count
        min_count = 1
        max_count = self.config.game_max_number
        self.correct_answer = random.randint(min_count, max_count)

        # Store image path for delayed display
        if self.available_images:
            self._current_image_path = random.choice(self.available_images)
        else:
            self._current_image_path = None

        # Show images after delay, then answers after another delay
        delay = self.config.game_delay
        self.after(delay, self._show_images)

    def _show_images(self) -> None:
        """Display images after initial delay."""
        if self._current_image_path:
            self._display_images(self._current_image_path, self.correct_answer)
        else:
            self._display_fallback_shapes(self.correct_answer)

        # Show answer buttons after another delay
        delay = self.config.game_delay
        self.after(delay, self._create_answer_buttons)

    def _calculate_groups(self, count: int) -> list[int]:
        """Calculate groups for displaying images.

        Groups help children understand number composition:
        - Even numbers: groups of 10, 4, 2
        - Odd numbers: after 10s, use 3+2 patterns (e.g., 5=3+2, 7=4+3, 9=4+3+2)
        """
        groups = []
        remaining = count

        # First, take as many 10s as possible
        while remaining >= 10:
            groups.append(10)
            remaining -= 10

        # Handle the remainder
        if remaining == 0:
            pass
        elif remaining % 2 == 0:  # Even remainder
            # Use groups of 4 and 2
            while remaining >= 4:
                groups.append(4)
                remaining -= 4
            while remaining >= 2:
                groups.append(2)
                remaining -= 2
        else:  # Odd remainder (1, 3, 5, 7, 9)
            # Special patterns to avoid 1 and show composition
            if remaining == 1:
                groups.append(1)
            elif remaining == 3:
                groups.append(3)
            elif remaining == 5:
                groups.append(3)
                groups.append(2)
            elif remaining == 7:
                groups.append(4)
                groups.append(3)
            elif remaining == 9:
                groups.append(4)
                groups.append(3)
                groups.append(2)

        return groups

    def _calculate_image_size(self, count: int, groups: list[int]) -> int:
        """Calculate appropriate image size based on count and available space."""
        base_size = self.config.game_image_size

        # Get available frame dimensions
        self.image_frame.update_idletasks()
        frame_height = self.image_frame.winfo_height()
        frame_width = self.image_frame.winfo_width()

        if frame_height < 50:  # Frame not yet sized
            frame_height = 400
        if frame_width < 50:
            frame_width = 800

        num_rows = len(groups) if groups else 1
        max_cols = max(groups) if groups else count

        # Calculate max size that fits vertically (with padding)
        vertical_padding = 10 * (num_rows + 1)  # pady between rows
        max_height_per_image = (
            (frame_height - vertical_padding) // num_rows if num_rows > 0 else base_size
        )

        # Calculate max size that fits horizontally (with padding)
        horizontal_padding = 6 * (max_cols + 1)  # padx between columns
        max_width_per_image = (
            (frame_width - horizontal_padding) // max_cols
            if max_cols > 0
            else base_size
        )

        # Use the smaller of the two to ensure it fits
        calculated_size = min(max_height_per_image, max_width_per_image, base_size)

        # Ensure minimum size
        return max(30, int(calculated_size * 0.9))  # 90% to leave some margin

    def _display_images(self, image_path: Path, count: int) -> None:
        """Display the specified image multiple times in educational groups."""
        try:
            # Calculate groups for educational display
            groups = self._calculate_groups(count)

            # Calculate appropriate image size
            img_size = self._calculate_image_size(count, groups)

            # Load image and resize preserving aspect ratio
            img = Image.open(image_path)

            # Calculate new size preserving aspect ratio
            width, height = img.size
            if width > height:
                new_width = img_size
                new_height = int(height * img_size / width)
            else:
                new_height = img_size
                new_width = int(width * img_size / height)

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Create a frame to hold images, centered in image_frame
            inner_frame = tk.Frame(self.image_frame, bg="#ecf0f1")
            inner_frame.grid(row=0, column=0)  # Centered via grid config

            # Display images in groups (each group in a row)
            row_idx = 0
            for group_size in groups:
                # Create a frame for this group/row
                row_frame = tk.Frame(inner_frame, bg="#ecf0f1")
                row_frame.grid(row=row_idx, column=0, pady=3)

                for col_idx in range(group_size):
                    photo = ImageTk.PhotoImage(img)
                    self.images.append(photo)  # Keep reference

                    label = tk.Label(row_frame, image=photo, bg="#ecf0f1")
                    # Add extra padding after 5th image in groups of 10
                    gap = self.config.game_group_gap
                    padx_right = gap if (group_size == 10 and col_idx == 4) else 2
                    label.grid(row=0, column=col_idx, padx=(2, padx_right), pady=2)

                row_idx += 1

        except Exception as e:
            print(f"Error loading image: {e}")
            self._display_fallback_shapes(count)

    def _display_fallback_shapes(self, count: int) -> None:
        """Display colored circles as fallback when no images available."""
        # Calculate groups for educational display
        groups = self._calculate_groups(count)
        img_size = self._calculate_image_size(count, groups)

        inner_frame = tk.Frame(self.image_frame, bg="#ecf0f1")
        inner_frame.grid(row=0, column=0)  # Centered via grid config

        colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"]
        color_idx = 0

        # Display shapes in groups (each group in a row)
        row_idx = 0
        for group_size in groups:
            row_frame = tk.Frame(inner_frame, bg="#ecf0f1")
            row_frame.grid(row=row_idx, column=0, pady=3)

            for col_idx in range(group_size):
                canvas = tk.Canvas(
                    row_frame,
                    width=img_size,
                    height=img_size,
                    bg="#ecf0f1",
                    highlightthickness=0,
                )
                color = colors[color_idx % len(colors)]
                canvas.create_oval(
                    5, 5, img_size - 5, img_size - 5, fill=color, outline=""
                )
                # Add extra padding after 5th shape in groups of 10
                gap = self.config.game_group_gap
                padx_right = gap if (group_size == 10 and col_idx == 4) else 2
                canvas.grid(row=0, column=col_idx, padx=(2, padx_right), pady=2)
                color_idx += 1

            row_idx += 1

    def _create_answer_buttons(self) -> None:
        """Create three answer buttons with one correct answer."""
        # Generate wrong answers
        min_val = max(1, self.correct_answer - 3)
        max_val = self.correct_answer + 3

        wrong_answers = []
        while len(wrong_answers) < 2:
            num = random.randint(min_val, max_val)
            if num != self.correct_answer and num not in wrong_answers and num >= 1:
                wrong_answers.append(num)

        # Combine and shuffle
        answers = [self.correct_answer] + wrong_answers
        random.shuffle(answers)

        # Create buttons
        button_font = tkfont.Font(family="Arial", size=36, weight="bold")

        for answer in answers:
            btn = tk.Button(
                self.answer_frame,
                text=str(answer),
                font=button_font,
                width=4,
                height=1,
                bg="#3498db",
                fg="white",
                activebackground="#2980b9",
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                command=lambda a=answer: self._check_answer(a),
            )
            btn.pack(side="left", padx=20)
            self.answer_buttons.append(btn)

    def _check_answer(self, answer: int) -> None:
        """Check if the selected answer is correct."""
        is_correct = answer == self.correct_answer

        # Record history
        self.history.append(
            {
                "round": self.current_round,
                "correct_answer": self.correct_answer,
                "player_answer": answer,
                "is_correct": is_correct,
            }
        )

        # Update progress box
        self._update_progress_box(self.current_round, is_correct)

        # Disable all buttons
        for btn in self.answer_buttons:
            btn.config(state="disabled", cursor="")

        # Highlight buttons
        for btn in self.answer_buttons:
            btn_answer = int(btn.cget("text"))
            if btn_answer == self.correct_answer:
                btn.config(bg="#2ecc71")  # Green for correct
            elif btn_answer == answer and not is_correct:
                btn.config(bg="#e74c3c")  # Red for wrong selection

        # Play sound only for correct answers (positive reinforcement)
        if is_correct:
            self.controller.sound_player.play_random_from_folder(
                self.config.correct_sound_folder
            )

        # Schedule next round
        delay = self.config.game_delay
        self.after(delay, self._next_round)

    def _show_results(self) -> None:
        """Show the results screen."""
        self.controller.show_view("counting_results", history=self.history)


class CountingResultsView(BaseView):
    """Results view for the counting game."""

    def __init__(self, parent: tk.Widget, controller: "GameController"):
        super().__init__(parent, controller)
        self.history: list[dict] = []
        self.video_player: VideoPlayer | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the results UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # Title
        title_font = tkfont.Font(family="Arial", size=48, weight="bold")
        self.title_label = tk.Label(
            self, text="🏆", font=title_font, bg="#f0f0f0", fg="#2c3e50"
        )
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(30, 20))

        # Main content area (will hold results on left, video on right)
        self.content_frame = tk.Frame(self, bg="#f0f0f0")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Results area (left side)
        self.results_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        self.results_frame.grid(row=0, column=0, sticky="nsew", padx=10)

        # Video area (right side) - will be populated when needed
        self.video_container = tk.Frame(self.content_frame, bg="#f0f0f0")
        self.video_container.grid(row=0, column=1, sticky="nsew", padx=10)

        # Button area
        self.button_frame = tk.Frame(self, bg="#f0f0f0")
        self.button_frame.grid(row=2, column=0, pady=30)

        button_font = tkfont.Font(family="Arial", size=20, weight="bold")
        button_config = {
            "font": button_font,
            "width": 15,
            "height": 2,
            "relief": "flat",
            "cursor": "hand2",
        }

        # Play again button
        self.play_again_btn = tk.Button(
            self.button_frame,
            text="🔄",
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            activeforeground="white",
            command=self._on_play_again,
            **button_config,
        )
        self.play_again_btn.pack(side="left", padx=20)

        # Main menu button
        self.menu_btn = tk.Button(
            self.button_frame,
            text="🏠",
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            command=self._on_main_menu,
            **button_config,
        )
        self.menu_btn.pack(side="left", padx=20)

        # Exit button
        self.exit_btn = tk.Button(
            self.button_frame,
            text="🚪",
            bg="#e67e22",
            fg="white",
            activebackground="#d35400",
            activeforeground="white",
            command=self._on_exit,
            **button_config,
        )
        self.exit_btn.pack(side="left", padx=20)

    def _on_play_again(self) -> None:
        """Handle play again button."""
        self._stop_video()
        self.controller.show_view("counting")

    def _on_main_menu(self) -> None:
        """Handle main menu button."""
        self._stop_video()
        self.controller.show_view("main_menu")

    def _on_exit(self) -> None:
        """Handle exit button."""
        self._stop_video()
        self.controller.quit_game()

    def _stop_video(self) -> None:
        """Stop video playback if active."""
        if self.video_player is not None:
            self.video_player.stop()

    def _check_video_reward(self) -> bool:
        """Check if player qualifies for video reward."""
        total = len(self.history)
        wrong_count = sum(1 for h in self.history if not h["is_correct"])

        min_rounds = self.config.video_min_rounds
        max_wrong = self.config.video_max_wrong

        return total >= min_rounds and wrong_count <= max_wrong

    def show(self, history: list[dict] | None = None) -> None:
        """Display the results."""
        if history is not None:
            self.history = history

        # Stop any previously playing video
        self._stop_video()

        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        for widget in self.video_container.winfo_children():
            widget.destroy()

        # Calculate score
        correct_count = sum(1 for h in self.history if h["is_correct"])
        total = len(self.history)

        # Score label
        score_font = tkfont.Font(family="Arial", size=32, weight="bold")
        score_text = f"✅ {correct_count} / {total}"
        score_label = tk.Label(
            self.results_frame,
            text=score_text,
            font=score_font,
            bg="#f0f0f0",
            fg="#2ecc71",
        )
        score_label.pack(pady=(0, 30))

        # History display
        history_frame = tk.Frame(self.results_frame, bg="#f0f0f0")
        history_frame.pack()

        result_font = tkfont.Font(family="Arial", size=28, weight="bold")

        for idx, entry in enumerate(self.history):
            color = "#2ecc71" if entry["is_correct"] else "#e74c3c"

            frame = tk.Frame(history_frame, bg=color, padx=15, pady=10)
            row = idx // 5
            col = idx % 5
            frame.grid(row=row, column=col, padx=10, pady=10)

            # Show the correct answer
            label = tk.Label(
                frame,
                text=str(entry["correct_answer"]),
                font=result_font,
                bg=color,
                fg="white",
            )
            label.pack()

            # Show player's answer if wrong
            if not entry["is_correct"]:
                small_font = tkfont.Font(family="Arial", size=12)
                wrong_label = tk.Label(
                    frame,
                    text=f"({entry['player_answer']})",
                    font=small_font,
                    bg=color,
                    fg="white",
                )
                wrong_label.pack()

        # Check for video reward
        if self._check_video_reward():
            self._play_video_reward()

    def _play_video_reward(self) -> None:
        """Play a video reward if available."""
        self.video_player = VideoPlayer(self.video_container, self.config)

        if not self.video_player.is_available():
            return

        video_path = self.video_player.get_random_video()
        if video_path is None:
            return

        # Create video frame
        video_frame = self.video_player.create_frame(self.video_container)
        video_frame.pack(fill="both", expand=True, pady=20)

        # Start playback after a short delay to ensure frame is ready
        self.after(100, lambda: self.video_player.play(video_path))


class AdditionGameView(BaseView):
    """Addition game view where children learn to add numbers."""

    def __init__(self, parent: tk.Widget, controller: "GameController"):
        super().__init__(parent, controller)
        self.current_round = 0
        self.num1 = 0
        self.num2 = 0
        self.correct_answer = 0
        self.history: list[dict] = []
        self.images: list[ImageTk.PhotoImage] = []
        self.answer_buttons: list[tk.Button] = []
        self.available_images: list[Path] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the addition game UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=3)  # Image area (2/3 of remaining)
        self.grid_rowconfigure(2, weight=0)  # Answer area (fixed height)

        # Header with back button and round info
        header = tk.Frame(self, bg="#f0f0f0")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        header.grid_columnconfigure(1, weight=1)

        back_font = tkfont.Font(family="Arial", size=14)
        self.back_btn = tk.Button(
            header,
            text="⬅️",
            font=back_font,
            bg="#95a5a6",
            fg="white",
            relief="flat",
            cursor="hand2",
            command=lambda: self.controller.show_view("main_menu"),
        )
        self.back_btn.grid(row=0, column=0, sticky="w")

        # Progress boxes frame
        self.progress_frame = tk.Frame(header, bg="#f0f0f0")
        self.progress_frame.grid(row=0, column=1)
        self.progress_boxes: list[tk.Canvas] = []

        # Image display area
        self.image_frame = tk.Frame(self, bg="#ecf0f1")
        self.image_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.image_frame.grid_rowconfigure(0, weight=1)
        self.image_frame.grid_columnconfigure(0, weight=1)

        # Answer buttons area (centered)
        self.answer_frame = tk.Frame(self, bg="#f0f0f0")
        self.answer_frame.grid(row=2, column=0, pady=(10, 30))

    def _load_available_images(self) -> None:
        """Load list of available images from the images folder."""
        images_folder = self.config.images_folder
        self.available_images = []

        if images_folder.exists():
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp"]:
                self.available_images.extend(images_folder.glob(ext))

    def show(self) -> None:
        """Start a new addition game."""
        self._load_available_images()
        self.current_round = 0
        self.history = []
        self._init_progress_boxes()
        self._next_round()

    def _init_progress_boxes(self) -> None:
        """Initialize the progress boxes."""
        # Clear existing boxes
        for box in self.progress_boxes:
            box.destroy()
        self.progress_boxes.clear()

        # Create new boxes
        total_rounds = self.config.game_rounds
        box_size = 20
        for i in range(total_rounds):
            box = tk.Canvas(
                self.progress_frame,
                width=box_size,
                height=box_size,
                bg="#f0f0f0",
                highlightthickness=0,
            )
            box.create_rectangle(
                2,
                2,
                box_size - 2,
                box_size - 2,
                fill="#bdc3c7",  # Gray
                outline="#95a5a6",
                tags="box",
            )
            box.grid(row=0, column=i, padx=2)
            self.progress_boxes.append(box)

    def _update_progress_box(self, round_num: int, is_correct: bool) -> None:
        """Update a progress box color based on answer correctness."""
        if 0 < round_num <= len(self.progress_boxes):
            box = self.progress_boxes[round_num - 1]
            color = "#2ecc71" if is_correct else "#e74c3c"  # Green or Red
            box.delete("box")
            box_size = 20
            box.create_rectangle(
                2,
                2,
                box_size - 2,
                box_size - 2,
                fill=color,
                outline="#27ae60" if is_correct else "#c0392b",
                tags="box",
            )

    def _next_round(self) -> None:
        """Set up the next round."""
        self.current_round += 1
        total_rounds = self.config.game_rounds

        if self.current_round > total_rounds:
            self._show_results()
            return

        # Clear previous content
        for widget in self.image_frame.winfo_children():
            widget.destroy()
        self.images.clear()

        for widget in self.answer_frame.winfo_children():
            widget.destroy()
        self.answer_buttons.clear()

        # Generate two random numbers that add up to max_number or less
        max_sum = self.config.game_max_number
        self.correct_answer = random.randint(2, max_sum)  # At least 2 so we can split
        self.num1 = random.randint(1, self.correct_answer - 1)
        self.num2 = self.correct_answer - self.num1

        # Store image path for delayed display
        if self.available_images:
            self._current_image_path = random.choice(self.available_images)
        else:
            self._current_image_path = None

        # Show images after delay, then answers after another delay
        delay = self.config.game_delay
        self.after(delay, self._show_addition_images)

    def _show_addition_images(self) -> None:
        """Display addition images after initial delay."""
        if self._current_image_path:
            self._display_addition(self._current_image_path)
        else:
            self._display_addition_fallback()

        # Show answer buttons after another delay
        delay = self.config.game_delay
        self.after(delay, self._create_answer_buttons)

    def _calculate_image_size(self, total_count: int) -> int:
        """Calculate appropriate image size based on count and available space."""
        base_size = self.config.game_image_size

        # Get available frame dimensions
        self.image_frame.update_idletasks()
        frame_height = self.image_frame.winfo_height()
        frame_width = self.image_frame.winfo_width()

        if frame_height < 50:  # Frame not yet sized
            frame_height = 400
        if frame_width < 50:
            frame_width = 800

        # For addition view: numbers on top row, images below
        # Estimate: 2 rows max for images, need space for number labels (~80px) and plus/equals
        available_height = frame_height - 100  # Reserve for number labels
        max_rows = max(1, (max(self.num1, self.num2) + 4) // 5)  # Up to 5 per row
        max_height_per_image = available_height // max(max_rows, 1)

        # Width: need to fit both number groups + plus + equals + question
        # Each group max 5 wide, plus symbols take ~200px
        available_width = frame_width - 250  # Reserve for +, =, ?
        max_width_per_image = available_width // 10  # 5 per group, 2 groups

        # Use the smaller of the two to ensure it fits
        calculated_size = min(max_height_per_image, max_width_per_image, base_size)

        # Ensure minimum size
        return max(30, int(calculated_size * 0.85))

    def _display_addition(self, image_path: Path) -> None:
        """Display the addition with two groups of images."""
        try:
            total_count = self.num1 + self.num2
            img_size = self._calculate_image_size(total_count)

            # Load image and resize preserving aspect ratio
            img = Image.open(image_path)
            width, height = img.size
            if width > height:
                new_width = img_size
                new_height = int(height * img_size / width)
            else:
                new_height = img_size
                new_width = int(width * img_size / height)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Create main container centered via grid
            inner_frame = tk.Frame(self.image_frame, bg="#ecf0f1")
            inner_frame.grid(row=0, column=0)  # Centered via grid config

            number_font = tkfont.Font(family="Arial", size=36, weight="bold")
            plus_font = tkfont.Font(family="Arial", size=28, weight="bold")

            # First number and its images
            col = 0

            # Number 1
            num1_label = tk.Label(
                inner_frame,
                text=str(self.num1),
                font=number_font,
                bg="#ecf0f1",
                fg="#3498db",
            )
            num1_label.grid(row=0, column=col, padx=20, pady=10)

            # Images for num1
            img1_frame = tk.Frame(inner_frame, bg="#ecf0f1")
            img1_frame.grid(row=1, column=col, padx=20, pady=10)

            cols1 = min(self.num1, 5)
            for i in range(self.num1):
                photo = ImageTk.PhotoImage(img)
                self.images.append(photo)
                label = tk.Label(img1_frame, image=photo, bg="#ecf0f1")
                r = i // cols1
                c = i % cols1
                label.grid(row=r, column=c, padx=3, pady=3)

            col += 1

            # Plus sign
            plus_label = tk.Label(
                inner_frame, text="➕", font=plus_font, bg="#ecf0f1", fg="#2c3e50"
            )
            plus_label.grid(row=0, column=col, rowspan=2, padx=30, pady=10)

            col += 1

            # Number 2
            num2_label = tk.Label(
                inner_frame,
                text=str(self.num2),
                font=number_font,
                bg="#ecf0f1",
                fg="#3498db",
            )
            num2_label.grid(row=0, column=col, padx=20, pady=10)

            # Images for num2
            img2_frame = tk.Frame(inner_frame, bg="#ecf0f1")
            img2_frame.grid(row=1, column=col, padx=20, pady=10)

            cols2 = min(self.num2, 5)
            for i in range(self.num2):
                photo = ImageTk.PhotoImage(img)
                self.images.append(photo)
                label = tk.Label(img2_frame, image=photo, bg="#ecf0f1")
                r = i // cols2
                c = i % cols2
                label.grid(row=r, column=c, padx=3, pady=3)

            col += 1

            # Equals sign
            equals_label = tk.Label(
                inner_frame, text="=", font=number_font, bg="#ecf0f1", fg="#2c3e50"
            )
            equals_label.grid(row=0, column=col, rowspan=2, padx=30, pady=10)

            col += 1

            # Question mark (will be replaced by answer buttons)
            self.question_label = tk.Label(
                inner_frame, text="❓", font=number_font, bg="#ecf0f1", fg="#e74c3c"
            )
            self.question_label.grid(row=0, column=col, rowspan=2, padx=20, pady=10)

        except Exception as e:
            print(f"Error loading image: {e}")
            self._display_addition_fallback()

    def _display_addition_fallback(self) -> None:
        """Display addition with colored circles as fallback."""
        total_count = self.num1 + self.num2
        img_size = self._calculate_image_size(total_count)

        inner_frame = tk.Frame(self.image_frame, bg="#ecf0f1")
        inner_frame.grid(row=0, column=0)  # Centered via grid config

        number_font = tkfont.Font(family="Arial", size=36, weight="bold")
        plus_font = tkfont.Font(family="Arial", size=28, weight="bold")

        colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"]

        col = 0

        # Number 1
        num1_label = tk.Label(
            inner_frame,
            text=str(self.num1),
            font=number_font,
            bg="#ecf0f1",
            fg="#3498db",
        )
        num1_label.grid(row=0, column=col, padx=20, pady=10)

        # Circles for num1
        img1_frame = tk.Frame(inner_frame, bg="#ecf0f1")
        img1_frame.grid(row=1, column=col, padx=20, pady=10)

        cols1 = min(self.num1, 5)
        for i in range(self.num1):
            canvas = tk.Canvas(
                img1_frame,
                width=img_size,
                height=img_size,
                bg="#ecf0f1",
                highlightthickness=0,
            )
            color = colors[i % len(colors)]
            canvas.create_oval(5, 5, img_size - 5, img_size - 5, fill=color, outline="")
            r = i // cols1
            c = i % cols1
            canvas.grid(row=r, column=c, padx=3, pady=3)

        col += 1

        # Plus sign
        plus_label = tk.Label(
            inner_frame, text="➕", font=plus_font, bg="#ecf0f1", fg="#2c3e50"
        )
        plus_label.grid(row=0, column=col, rowspan=2, padx=30, pady=10)

        col += 1

        # Number 2
        num2_label = tk.Label(
            inner_frame,
            text=str(self.num2),
            font=number_font,
            bg="#ecf0f1",
            fg="#3498db",
        )
        num2_label.grid(row=0, column=col, padx=20, pady=10)

        # Circles for num2
        img2_frame = tk.Frame(inner_frame, bg="#ecf0f1")
        img2_frame.grid(row=1, column=col, padx=20, pady=10)

        cols2 = min(self.num2, 5)
        for i in range(self.num2):
            canvas = tk.Canvas(
                img2_frame,
                width=img_size,
                height=img_size,
                bg="#ecf0f1",
                highlightthickness=0,
            )
            color = colors[(i + self.num1) % len(colors)]
            canvas.create_oval(5, 5, img_size - 5, img_size - 5, fill=color, outline="")
            r = i // cols2
            c = i % cols2
            canvas.grid(row=r, column=c, padx=3, pady=3)

        col += 1

        # Equals sign
        equals_label = tk.Label(
            inner_frame, text="=", font=number_font, bg="#ecf0f1", fg="#2c3e50"
        )
        equals_label.grid(row=0, column=col, rowspan=2, padx=30, pady=10)

        col += 1

        # Question mark
        self.question_label = tk.Label(
            inner_frame, text="❓", font=number_font, bg="#ecf0f1", fg="#e74c3c"
        )
        self.question_label.grid(row=0, column=col, rowspan=2, padx=20, pady=10)

    def _create_answer_buttons(self) -> None:
        """Create three answer buttons with one correct answer."""
        # Generate wrong answers
        max_sum = self.config.game_max_number
        min_val = max(2, self.correct_answer - 3)
        max_val = min(max_sum + 2, self.correct_answer + 3)

        wrong_answers = []
        while len(wrong_answers) < 2:
            num = random.randint(min_val, max_val)
            if num != self.correct_answer and num not in wrong_answers and num >= 1:
                wrong_answers.append(num)

        # Combine and shuffle
        answers = [self.correct_answer] + wrong_answers
        random.shuffle(answers)

        # Create buttons
        button_font = tkfont.Font(family="Arial", size=36, weight="bold")
        button_color = self.config.game_button_color

        for answer in answers:
            btn = tk.Button(
                self.answer_frame,
                text=str(answer),
                font=button_font,
                width=4,
                height=1,
                bg=button_color,
                fg="white",
                activebackground=button_color,
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                command=lambda a=answer: self._check_answer(a),
            )
            btn.pack(side="left", padx=20)
            self.answer_buttons.append(btn)

    def _check_answer(self, answer: int) -> None:
        """Check if the selected answer is correct."""
        is_correct = answer == self.correct_answer

        # Record history
        self.history.append(
            {
                "round": self.current_round,
                "num1": self.num1,
                "num2": self.num2,
                "correct_answer": self.correct_answer,
                "player_answer": answer,
                "is_correct": is_correct,
            }
        )

        # Update progress box
        self._update_progress_box(self.current_round, is_correct)

        # Disable all buttons
        for btn in self.answer_buttons:
            btn.config(state="disabled", cursor="")

        # Highlight buttons
        for btn in self.answer_buttons:
            btn_answer = int(btn.cget("text"))
            if btn_answer == self.correct_answer:
                btn.config(bg="#2ecc71")  # Green for correct
            elif btn_answer == answer and not is_correct:
                btn.config(bg="#e74c3c")  # Red for wrong selection

        # Play sound only for correct answers (positive reinforcement)
        if is_correct:
            self.controller.sound_player.play_random_from_folder(
                self.config.correct_sound_folder
            )

        # Schedule next round
        delay = self.config.game_delay
        self.after(delay, self._next_round)

    def _show_results(self) -> None:
        """Show the results screen."""
        self.controller.show_view("addition_results", history=self.history)


class AdditionResultsView(BaseView):
    """Results view for the addition game."""

    def __init__(self, parent: tk.Widget, controller: "GameController"):
        super().__init__(parent, controller)
        self.history: list[dict] = []
        self.video_player: VideoPlayer | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the results UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # Title
        title_font = tkfont.Font(family="Arial", size=48, weight="bold")
        self.title_label = tk.Label(
            self, text="🏆", font=title_font, bg="#f0f0f0", fg="#2c3e50"
        )
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(30, 20))

        # Main content area (will hold results on left, video on right)
        self.content_frame = tk.Frame(self, bg="#f0f0f0")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Results area (left side)
        self.results_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        self.results_frame.grid(row=0, column=0, sticky="nsew", padx=10)

        # Video area (right side) - will be populated when needed
        self.video_container = tk.Frame(self.content_frame, bg="#f0f0f0")
        self.video_container.grid(row=0, column=1, sticky="nsew", padx=10)

        # Button area
        self.button_frame = tk.Frame(self, bg="#f0f0f0")
        self.button_frame.grid(row=2, column=0, pady=30)

        button_font = tkfont.Font(family="Arial", size=20, weight="bold")
        button_config = {
            "font": button_font,
            "width": 15,
            "height": 2,
            "relief": "flat",
            "cursor": "hand2",
        }

        # Play again button
        self.play_again_btn = tk.Button(
            self.button_frame,
            text="🔄",
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            activeforeground="white",
            command=self._on_play_again,
            **button_config,
        )
        self.play_again_btn.pack(side="left", padx=20)

        # Main menu button
        self.menu_btn = tk.Button(
            self.button_frame,
            text="🏠",
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            command=self._on_main_menu,
            **button_config,
        )
        self.menu_btn.pack(side="left", padx=20)

        # Exit button
        self.exit_btn = tk.Button(
            self.button_frame,
            text="🚪",
            bg="#e67e22",
            fg="white",
            activebackground="#d35400",
            activeforeground="white",
            command=self._on_exit,
            **button_config,
        )
        self.exit_btn.pack(side="left", padx=20)

    def _on_play_again(self) -> None:
        """Handle play again button."""
        self._stop_video()
        self.controller.show_view("addition")

    def _on_main_menu(self) -> None:
        """Handle main menu button."""
        self._stop_video()
        self.controller.show_view("main_menu")

    def _on_exit(self) -> None:
        """Handle exit button."""
        self._stop_video()
        self.controller.quit_game()

    def _stop_video(self) -> None:
        """Stop video playback if active."""
        if self.video_player is not None:
            self.video_player.stop()

    def _check_video_reward(self) -> bool:
        """Check if player qualifies for video reward."""
        total = len(self.history)
        wrong_count = sum(1 for h in self.history if not h["is_correct"])

        min_rounds = self.config.video_min_rounds
        max_wrong = self.config.video_max_wrong

        return total >= min_rounds and wrong_count <= max_wrong

    def show(self, history: list[dict] | None = None) -> None:
        """Display the results."""
        if history is not None:
            self.history = history

        # Stop any previously playing video
        self._stop_video()

        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        for widget in self.video_container.winfo_children():
            widget.destroy()

        # Calculate score
        correct_count = sum(1 for h in self.history if h["is_correct"])
        total = len(self.history)

        # Score label
        score_font = tkfont.Font(family="Arial", size=32, weight="bold")
        score_text = f"✅ {correct_count} / {total}"
        score_label = tk.Label(
            self.results_frame,
            text=score_text,
            font=score_font,
            bg="#f0f0f0",
            fg="#2ecc71",
        )
        score_label.pack(pady=(0, 30))

        # History display
        history_frame = tk.Frame(self.results_frame, bg="#f0f0f0")
        history_frame.pack()

        result_font = tkfont.Font(family="Arial", size=20, weight="bold")

        for idx, entry in enumerate(self.history):
            color = "#2ecc71" if entry["is_correct"] else "#e74c3c"

            frame = tk.Frame(history_frame, bg=color, padx=15, pady=10)
            row = idx // 5
            col = idx % 5
            frame.grid(row=row, column=col, padx=5, pady=10)

            # Show the equation
            equation = f"{entry['num1']}+{entry['num2']}={entry['correct_answer']}"
            label = tk.Label(
                frame,
                text=equation,
                font=result_font,
                bg=color,
                fg="white",
            )
            label.pack()

        # Check for video reward
        if self._check_video_reward():
            self._play_video_reward()

    def _play_video_reward(self) -> None:
        """Play a video reward if available."""
        self.video_player = VideoPlayer(self.video_container, self.config)

        if not self.video_player.is_available():
            return

        video_path = self.video_player.get_random_video()
        if video_path is None:
            return

        # Create video frame
        video_frame = self.video_player.create_frame(self.video_container)
        video_frame.pack(fill="both", expand=True, pady=20)

        # Start playback after a short delay to ensure frame is ready
        self.after(100, lambda: self.video_player.play(video_path))


class GameController:
    """Main game controller managing views and game state."""

    def __init__(self, root: tk.Tk, config: Config):
        self.root = root
        self.config = config
        self.sound_player = SoundPlayer(config.sound_enabled)

        # Pre-initialize VLC so first video playback is instant
        VideoPlayer.warmup()

        # Configure main window
        self._setup_window()

        # Container for views
        self.container = tk.Frame(root)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Create views
        self.views: dict[str, BaseView] = {}
        self._create_views()

        # Show main menu
        self.current_view: BaseView | None = None
        self.show_view("main_menu")

    def _setup_window(self) -> None:
        """Set up the main window."""
        self.root.title(self.config.title)

        # Start maximized
        self.root.state("zoomed")

        if self.config.fullscreen:
            self.root.attributes("-fullscreen", True)

        self.root.configure(bg="#f0f0f0")

        # Handle escape key to exit fullscreen or quit
        self.root.bind("<Escape>", self._on_escape)

    def _on_escape(self, event: tk.Event) -> None:
        """Handle escape key press."""
        if self.config.fullscreen:
            self.root.attributes("-fullscreen", False)
        else:
            self.root.quit()

    def quit_game(self) -> None:
        """Quit the game."""
        self.root.quit()

    def _create_views(self) -> None:
        """Create all game views."""
        view_classes = {
            "main_menu": MainMenuView,
            "settings": SettingsView,
            "counting": CountingGameView,
            "counting_results": CountingResultsView,
            "addition": AdditionGameView,
            "addition_results": AdditionResultsView,
        }

        for name, view_class in view_classes.items():
            view = view_class(self.container, self)
            view.grid(row=0, column=0, sticky="nsew")
            self.views[name] = view

    def show_view(self, view_name: str, **kwargs) -> None:
        """Show a specific view.

        Args:
            view_name: Name of the view to show
            **kwargs: Additional arguments to pass to the view's show method
        """
        if view_name not in self.views:
            print(f"Unknown view: {view_name}")
            return

        # Hide current view
        if self.current_view is not None:
            self.current_view.hide()

        # Show new view
        view = self.views[view_name]
        view.tkraise()
        view.show(**kwargs)
        self.current_view = view


def run_game(config: Config | None = None) -> None:
    """Run the MyMath game.

    Args:
        config: Optional Config instance. If None, will load from default location.
    """
    if config is None:
        config = get_config()

    root = tk.Tk()

    # Try to set icon if available
    icon_path = config.get_path("icon_image")
    if icon_path.exists():
        try:
            icon = ImageTk.PhotoImage(Image.open(icon_path))
            root.iconphoto(True, icon)
        except Exception:
            pass

    controller = GameController(root, config)
    root.mainloop()
