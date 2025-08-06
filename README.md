# 🤖 Hand Game - AI Learning Finger Counter

A fun computer vision game where you compete against an AI robot that learns your patterns and gets smarter over time!

## 🎮 What is this?

Ever played "Odds or Evens" with your fingers? This is that game, 
but with a twist - you're playing against a robot that actually learns how you play. Show 1-5 fingers to your webcam, pick odds or evens, and see if you can outsmart an AI that's studying your moves.
The robot gets smarter with every game, learning your patterns, preferences.

## ✨ Features

- **Real-time hand detection** using MediaPipe - just show your fingers to the camera
- **AI opponent that learns** - uses River ML to analyze your playing patterns
- **Hardware integration** - optional Arduino with LEDs, buzzer, and LCD messages
- **Robot simulation window** - see your AI opponent in a separate pygame window
- **Video overlays** - watch the robot show its fingers in real-time
- **Best of 3 format** - first to win 2 rounds takes the game
- **Data persistence** - the AI remembers you across sessions

## 🎯 How to Play

1. **Start the game** - Press SPACE to begin
2. **Choose your strategy** - Press 'O' for ODDS or 'E' for EVENS
3. **Wait for countdown** - 3-2-1-GO! (with LED effects if you have Arduino)
4. **Show your fingers** - Display 1-5 fingers when the countdown ends
5. **See who wins** - If the total fingers matches your choice, you win!

The AI analyzes your patterns and tries to predict what you'll do next. The more you play, the smarter it gets!

## 🛠️ Installation

### Prerequisites
- Python 3.7+
- Webcam
- (Optional) Arduino Uno with LEDs, buzzer, and LCD

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/hand-game.git
   cd hand-game
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Optional: Set up Arduino** (see [Arduino Setup Guide](Other/ARDUINO_SETUP.md))
   - Connect LEDs, buzzer, and LCD to Arduino
   - Upload `arduino_game_controller.ino` to your Arduino
   - The game will auto-detect your Arduino

4. **Run the game**
   ```bash
   python main.py
   ```

## 🎮 Controls

- **SPACE** - Start game / Next round
- **O** - Choose ODDS
- **E** - Choose EVENS
- **ESC** - Exit current game
- **Q** - Quit application
- **Arduino Button** - Alternative spacebar (if connected)

## 🤖 The AI System

The robot uses machine learning to:
- **Predict your finger count** (1-5) based on your history
- **Guess your odds/evens choice** from your patterns
- **Adapt its strategy** to try to beat you
- **Learn continuously** - gets smarter with every round

The AI analyzes:
- Your recent finger choices
- Your odds/evens preferences
- Win/loss patterns
- Time of day and game context
- How you change strategies

## 🔧 Technical Details

### Core Technologies
- **Computer Vision**: MediaPipe for hand landmark detection
- **Machine Learning**: River ML for online learning
- **Hardware**: Arduino integration with PySerial
- **Graphics**: OpenCV for video processing, Pygame for simulation
- **Data**: JSON storage for game history, Pickle for AI models

### Architecture
- **Modular design** - each component handles its own responsibility
- **Thread-safe** - countdown and video playback run in background
- **Real-time performance** - 30+ FPS hand detection
- **Cross-platform** - works on Windows, Mac, and Linux

## 📁 Project Structure

```
Hand Game/
├── main.py                      # Game entry point
├── game_engine.py               # Core game logic
├── hand_detector.py             # Computer vision
├── ai_predictor.py              # Machine learning
├── arduino_controller.py        # Hardware interface
├── ui_manager.py                # User interface
├── video_manager.py             # Video overlays
├── pygame_simulator.py          # Robot simulation
├── config.py                    # Settings
├── arduino_game_controller.ino  # Arduino firmware
├── data/                        # Game data storage
├── videos/                      # Robot video assets
└── Other/                       # Documentation
```

## 🎨 Customization

### Adding Robot Videos
Place your robot videos in the `videos/` folder:
- `robot_1_finger.mp4` through `robot_5_fingers.mp4`
- `robot_wins.mp4` and `robot_loses.mp4`

### Modifying AI Behavior
Edit `ai_predictor.py` to change how the robot learns and predicts.

### Arduino Customization
Modify `arduino_game_controller.ino` to add new LED patterns or LCD messages.

## 📈 Future Ideas
- **Multiplayer mode** with network support
- **Advanced gestures** (rock-paper-scissors expansion)
- **Physical robot arm** integration