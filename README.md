# MyMath 🔢

A fun, interactive math learning game designed for young children (ages 3+). The game uses visual representations and positive reinforcement to teach counting and basic addition.

## Author

Mauricio Fernández

## Features

- **🔢 Counting Mode**: Learn to count by identifying how many objects are displayed
- **➕ Addition Mode**: Learn basic addition with visual representations
- **➖ Subtraction Mode**: Learn subtraction with visual hints for removed items
- **⬜⬜ Multiplication Exploration**: Explore multiplication as repeated visual groups
- **✖️ Multiplication Mode**: Solve multiplication exercises with answer buttons
- **🖼️ Visual Learning**: Uses images grouped in educational patterns (groups of 2, 3, 4, 5, 10)
- **🔊 Positive Reinforcement**: Sound effects for correct answers only
- **🌍 Language Independent**: Uses symbols instead of text for universal accessibility
- **⚙️ Configurable**: Easy YAML configuration for customization

## Installation

### Requirements

- Python 3.9 or higher
- Windows (for sound support via winsound)

### Setup

1. Download or clone the repository
2. Run `install.bat` (double-click)

The installer will:
- Create a virtual environment
- Install all dependencies
- Create `config.yaml` from the example template
- Create a desktop shortcut

## Usage

Double-click the **MyMath** shortcut on your desktop to start the game.

## Configuration

Edit `config.yaml` to customize the game:

```yaml
# Game title and icon
title: "MyMath"
icon_image: "data/icon/icon.png"

# Folders for images and sounds
images_folder: "data/images"
sound:
  enabled: true
  correct_sound: "data/reactions"  # Folder with sound files

# Game settings
game:
  max_number: 10      # Maximum number for counting/addition
  rounds: 10          # Rounds per game session
  image_size: 150     # Image size in pixels
  delay_ms: 1000      # Delay between stages
  hint_delay_ms: 3000 # Delay before showing hints
  color1: "#4C7CF0"   # First number color
  color2: "#F4A261"   # Second number and hint border color
  color3: "#2EC4B6"   # Result and answer button color
  unknown_symbol: "x" # Placeholder for unknown results in arithmetic modes
  correct_color: "#00FF00"   # Correct answer feedback color
  incorrect_color: "#FDE68A" # Incorrect answer feedback color
```

## Project Structure

```
MyMath/
├── config.yaml          # Game configuration
├── pyproject.toml       # Project metadata
├── src/
│   └── my_math/
│       ├── __init__.py
│       ├── __main__.py  # Entry point
│       ├── config.py    # Configuration loader
│       └── game.py      # Main game logic
└── data/
    ├── images/          # Count/addition images
    ├── reactions/       # Correct answer sounds
    └── sounds/          # Other sounds
```

## Game Modes

### Counting Mode 🔢
- Displays a random number of images
- Images are grouped educationally (e.g., 7 = 4 + 3)
- Child selects the correct count from 3 options

### Addition Mode ➕
- Shows two groups of images with numbers
- Displays: `num1 + num2 = ?`
- Child selects the correct sum from 3 options

### Subtraction Mode ➖
- Shows the minuend and subtrahend visually
- Reveals hint borders after a delay so the removed group is easy to see
- Child selects the correct difference from 3 options

### Multiplication Exploration ⬜⬜
- Shows multiplication as repeated rows of the same image
- Lets children adjust both factors and see the product update immediately

### Multiplication Mode ✖️
- Generates multiplication exercises using the configured maximum number for both factors
- Shows the multiplication as repeated visual groups with smaller images so the full task stays on screen
- Child selects the correct product from 3 options

## Progress Tracking

- Visual progress boxes show completed rounds
- Green = correct answer
- Red = incorrect answer
- Results summary at end of each session

## License

MIT License
