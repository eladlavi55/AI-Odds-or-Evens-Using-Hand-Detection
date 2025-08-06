import os

# handle Unicode characters properly on Windows
try:
    from unicode_fix import safe_print, initialize_unicode
    # set up Unicode when this file loads
    initialize_unicode()
except ImportError:
    # backup print function if unicode_fix isn't there
    def safe_print(*args, **kwargs):
        try:
            print(*args, **kwargs)
        except UnicodeEncodeError:
            # just strip out weird characters if printing fails
            safe_args = []
            for arg in args:
                if isinstance(arg, str):
                    safe_args.append(arg.encode('ascii', errors='replace').decode('ascii'))
                else:
                    safe_args.append(str(arg))
            print(*safe_args, **kwargs)

# main game settings
GAME_CONFIG = {
    'MAX_ROUNDS': 3,
    'CAMERA_WIDTH': 1024,
    'CAMERA_HEIGHT': 768,
    'MIN_DETECTION_CONFIDENCE': 0.5,
    'MIN_TRACKING_CONFIDENCE': 0.5,
    'VIDEO_DISPLAY_WIDTH': 300,
    'VIDEO_DISPLAY_HEIGHT': 225,
    'VIDEO_POSITION_X': 650,  # position of video overlay (right side of enlarged window)
    'VIDEO_POSITION_Y': 200,  # below the top UI elements
    
    # robot simulation window settings
    'PYGAME_SIMULATION_ENABLED': True,
    'PYGAME_WINDOW_WIDTH': 400,
    'PYGAME_WINDOW_HEIGHT': 300,
    'PYGAME_WINDOW_TITLE': 'Robot Simulation',
}

# file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
VIDEO_DIR = os.path.join(BASE_DIR, 'videos')

# create folders if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# data files
GAME_HISTORY_FILE = os.path.join(DATA_DIR, 'game_history.json')
AI_MODEL_FILE = os.path.join(DATA_DIR, 'ai_model.pkl')
STATISTICS_FILE = os.path.join(DATA_DIR, 'statistics.json')

# where to find the robot videos
VIDEO_PATHS = {
    'robot_fingers': {
        1: os.path.join(VIDEO_DIR, 'robot_1_finger.mp4'),
        2: os.path.join(VIDEO_DIR, 'robot_2_fingers.mp4'),
        3: os.path.join(VIDEO_DIR, 'robot_3_fingers.mp4'),
        4: os.path.join(VIDEO_DIR, 'robot_4_fingers.mp4'),
        5: os.path.join(VIDEO_DIR, 'robot_5_fingers.mp4'),
    },
    'robot_reactions': {
        'win': os.path.join(VIDEO_DIR, 'robot_wins.mp4'),
        'lose': os.path.join(VIDEO_DIR, 'robot_loses.mp4'),
    }
}

# ui colors
COLORS = {
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'RED': (0, 0, 255),
    'GREEN': (0, 255, 0),
    'BLUE': (255, 0, 0),
    'YELLOW': (0, 255, 255),
    'CYAN': (255, 255, 0),
    'MAGENTA': (255, 0, 255),
} 