"""Main game module for MyMath - A math learning game for children."""

import os
import random
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont
from typing import Callable

from PIL import Image, ImageTk

from .config import get_config, Config


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
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # Icon image
        self.icon_image = None
        icon_path = self.config.get_path("icon_image")
        if icon_path.exists():
            try:
                img = Image.open(icon_path)
                img = img.resize((120, 120), Image.Resampling.LANCZOS)
                self.icon_image = ImageTk.PhotoImage(img)
                icon_label = tk.Label(self, image=self.icon_image, bg="#f0f0f0")
                icon_label.grid(row=0, column=0, pady=(30, 10))
            except Exception:
                pass

        # Title
        title_font = tkfont.Font(family="Arial", size=48, weight="bold")
        self.title_label = tk.Label(
            self, text=self.config.title, font=title_font, bg="#f0f0f0", fg="#2c3e50"
        )
        self.title_label.grid(row=1, column=0, pady=(10, 30))

        # Button frame
        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.grid(row=3, column=0, pady=20)

        # Button style
        button_font = tkfont.Font(family="Arial", size=24, weight="bold")
        button_config = {
            "font": button_font,
            "width": 15,
            "height": 2,
            "relief": "flat",
            "cursor": "hand2",
        }

        # Counting game button
        self.counting_btn = tk.Button(
            button_frame,
            text="🔢  1 2 3",
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            command=lambda: self.controller.show_view("counting"),
            **button_config,
        )
        self.counting_btn.pack(pady=15)

        # Second game mode button (placeholder for now)
        self.game2_btn = tk.Button(
            button_frame,
            text="➕ ➖ ✖️ ➗",
            bg="#9b59b6",
            fg="white",
            activebackground="#8e44ad",
            activeforeground="white",
            command=lambda: None,  # Placeholder
            state="disabled",
            **button_config,
        )
        self.game2_btn.pack(pady=15)

    def show(self) -> None:
        """Update title when shown (in case config changed)."""
        self.title_label.config(text=self.config.title)


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
        self.grid_rowconfigure(1, weight=2)  # Image area
        self.grid_rowconfigure(2, weight=1)  # Answer area

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

        round_font = tkfont.Font(family="Arial", size=18, weight="bold")
        self.round_label = tk.Label(
            header, text="1 / 5", font=round_font, bg="#f0f0f0", fg="#2c3e50"
        )
        self.round_label.grid(row=0, column=1)

        # Image display area
        self.image_frame = tk.Frame(self, bg="#ecf0f1")
        self.image_frame.grid(row=1, column=0, sticky="nsew", padx=40, pady=20)

        # Answer buttons area
        self.answer_frame = tk.Frame(self, bg="#f0f0f0")
        self.answer_frame.grid(row=2, column=0, pady=30)

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
        self._next_round()

    def _next_round(self) -> None:
        """Set up the next round."""
        self.current_round += 1
        total_rounds = self.config.counting_rounds

        if self.current_round > total_rounds:
            self._show_results()
            return

        # Update round label
        self.round_label.config(text=f"{self.current_round} / {total_rounds}")

        # Clear previous images
        for widget in self.image_frame.winfo_children():
            widget.destroy()
        self.images.clear()

        # Clear previous answer buttons
        for widget in self.answer_frame.winfo_children():
            widget.destroy()
        self.answer_buttons.clear()

        # Generate random count
        min_count = self.config.counting_min_count
        max_count = self.config.counting_max_count
        self.correct_answer = random.randint(min_count, max_count)

        # Select random image
        if self.available_images:
            image_path = random.choice(self.available_images)
            self._display_images(image_path, self.correct_answer)
        else:
            # Fallback: display colored circles if no images
            self._display_fallback_shapes(self.correct_answer)

        # Create answer buttons after a delay
        delay = self.config.counting_numbers_delay
        self.after(delay, self._create_answer_buttons)

    def _display_images(self, image_path: Path, count: int) -> None:
        """Display the specified image multiple times."""
        try:
            # Load and resize image
            img = Image.open(image_path)
            size = self.config.counting_image_size
            img = img.resize((size, size), Image.Resampling.LANCZOS)

            # Create a frame to hold images in a grid
            inner_frame = tk.Frame(self.image_frame, bg="#ecf0f1")
            inner_frame.place(relx=0.5, rely=0.5, anchor="center")

            # Calculate grid layout
            cols = min(count, 5)  # Max 5 per row
            rows = (count + cols - 1) // cols

            for i in range(count):
                photo = ImageTk.PhotoImage(img)
                self.images.append(photo)  # Keep reference

                label = tk.Label(inner_frame, image=photo, bg="#ecf0f1")
                row = i // cols
                col = i % cols
                label.grid(row=row, column=col, padx=10, pady=10)

        except Exception as e:
            print(f"Error loading image: {e}")
            self._display_fallback_shapes(count)

    def _display_fallback_shapes(self, count: int) -> None:
        """Display colored circles as fallback when no images available."""
        inner_frame = tk.Frame(self.image_frame, bg="#ecf0f1")
        inner_frame.place(relx=0.5, rely=0.5, anchor="center")

        colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"]
        size = self.config.counting_image_size

        cols = min(count, 5)

        for i in range(count):
            canvas = tk.Canvas(
                inner_frame, width=size, height=size, bg="#ecf0f1", highlightthickness=0
            )
            color = colors[i % len(colors)]
            canvas.create_oval(5, 5, size - 5, size - 5, fill=color, outline="")

            row = i // cols
            col = i % cols
            canvas.grid(row=row, column=col, padx=10, pady=10)

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
            self.controller.sound_player.play(self.config.correct_sound)

        # Schedule next round
        delay = self.config.counting_next_round_delay
        self.after(delay, self._next_round)

    def _show_results(self) -> None:
        """Show the results screen."""
        self.controller.show_view("counting_results", history=self.history)


class CountingResultsView(BaseView):
    """Results view for the counting game."""

    def __init__(self, parent: tk.Widget, controller: "GameController"):
        super().__init__(parent, controller)
        self.history: list[dict] = []
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
        self.title_label.grid(row=0, column=0, pady=(30, 20))

        # Results area
        self.results_frame = tk.Frame(self, bg="#f0f0f0")
        self.results_frame.grid(row=1, column=0, sticky="nsew", padx=50)

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
            command=lambda: self.controller.show_view("counting"),
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
            command=lambda: self.controller.show_view("main_menu"),
            **button_config,
        )
        self.menu_btn.pack(side="left", padx=20)

    def show(self, history: list[dict] | None = None) -> None:
        """Display the results."""
        if history is not None:
            self.history = history

        # Clear previous results
        for widget in self.results_frame.winfo_children():
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

        for entry in self.history:
            color = "#2ecc71" if entry["is_correct"] else "#e74c3c"

            frame = tk.Frame(history_frame, bg=color, padx=15, pady=10)
            frame.pack(side="left", padx=10, pady=10)

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
                    text=f"(du: {entry['player_answer']})",
                    font=small_font,
                    bg=color,
                    fg="white",
                )
                wrong_label.pack()


class GameController:
    """Main game controller managing views and game state."""

    def __init__(self, root: tk.Tk, config: Config):
        self.root = root
        self.config = config
        self.sound_player = SoundPlayer(config.sound_enabled)

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

    def _create_views(self) -> None:
        """Create all game views."""
        view_classes = {
            "main_menu": MainMenuView,
            "counting": CountingGameView,
            "counting_results": CountingResultsView,
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
