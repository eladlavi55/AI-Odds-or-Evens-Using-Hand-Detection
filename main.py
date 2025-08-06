#!/usr/bin/env python3
"""
Odds or Evens finger counting game with AI learning

A fun game where you show fingers to a webcam and try to beat
a robot that learns how you play over time.

Basic idea: Show 1-5 fingers, pick odds/evens, robot does same.
If the total matches your pick, you win that round.

Uses MediaPipe for hand tracking, River ML for the AI brain.
Also has Arduino support for LEDs and LCD messages.

Controls: SPACE=start, O=odds, E=evens, ESC=exit, Q=quit

Need: opencv-python, mediapipe, numpy, pygame
Optional: river (for smarter AI)
"""

import cv2
import sys
import traceback
from config import GAME_CONFIG, safe_print
from game_engine import GameEngine
from pygame_simulator import PygameSimulator

def main():
    """Main game entry point"""
    safe_print("="*60)
    safe_print("[GAME] ODDS OR EVENS HAND GAME WITH AI [ROBOT]")
    safe_print("="*60)
    safe_print("[DEBUG] Running fixed version with 0-finger exploit patched")
    safe_print("initializing game components...")
    
    # get webcam ready
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        safe_print("[ERROR] Cannot access camera!")
        safe_print("Please check your camera connection and permissions.")
        return
    
    # set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, GAME_CONFIG['CAMERA_WIDTH'])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, GAME_CONFIG['CAMERA_HEIGHT'])
    
    # start up the main game engine
    try:
        game_engine = GameEngine()
    except Exception as e:
        safe_print(f"[ERROR] Error initializing game engine: {e}")
        safe_print("Make sure all dependencies are installed:")
        safe_print("  pip install opencv-python mediapipe numpy pygame")
        safe_print("  pip instaOpen VS Code Settingsll river  # Optional, for AI learning")
        return
    
    # start pygame window if we want it
    pygame_sim = None
    if GAME_CONFIG.get('PYGAME_SIMULATION_ENABLED', False):
        try:
            pygame_sim = PygameSimulator(
                width=GAME_CONFIG['PYGAME_WINDOW_WIDTH'],
                height=GAME_CONFIG['PYGAME_WINDOW_HEIGHT'],
                title=GAME_CONFIG['PYGAME_WINDOW_TITLE']
            )
            pygame_sim.start_thread()
            game_engine.set_pygame_simulator(pygame_sim)
            safe_print("[SUCCESS] Pygame robot simulator initialized!")
        except Exception as e:
            safe_print(f"[WARNING] Could not initialize pygame simulator: {e}")
            safe_print("Game will continue without robot simulation window")
            pygame_sim = None
    
    safe_print("[SUCCESS] Game initialized successfully!")
    safe_print("\n[INFO] GAME INSTRUCTIONS:")
    safe_print("- Press SPACE to start game")
    safe_print("- Press 'O' for ODDS, 'E' for EVENS")
    safe_print("- Show 1-5 fingers when countdown ends")
    safe_print("- Press ESC to exit current game")
    safe_print("- Press Q to quit application")
    safe_print("\n[INFO] The AI will learn your patterns and get smarter over time!")
    safe_print("[DATA] Check the terminal for AI predictions and analysis")
    safe_print("[SAVE] Game data is saved in the 'data' folder")
    safe_print("[VIDEO] Robot videos are stored in the 'videos' folder")
    safe_print("\n" + "="*60)
    
    try:
        # main loop - runs until user quits
        while True:
            ret, frame = cap.read()
            if not ret:
                safe_print("[ERROR] Error reading from camera")
                break
            
            # mirror the image so it feels natural
            frame = cv2.flip(frame, 1)
            
            # let the game engine handle this frame
            frame = game_engine.process_frame(frame)
            
            # display it
            cv2.imshow('Odds or Evens Game with AI', frame)
            
            # check for key presses
            key = cv2.waitKey(1) & 0xFF
            if key != 255:  # someone pressed something
                result = game_engine.handle_keypress(key)
                if result == 'quit':
                    break
    
    except KeyboardInterrupt:
        safe_print("\n[STOP] Game interrupted by user")
    except Exception as e:
        safe_print(f"\n[ERROR] Unexpected error: {e}")
        safe_print("Stack trace:")
        traceback.print_exc()
    
    finally:
        # clean up everything
        safe_print("\n[CLEANUP] Cleaning up...")
        cap.release()
        cv2.destroyAllWindows()  # close all OpenCV windows
        
        # close pygame if it's running
        if pygame_sim:
            try:
                # try to close it nicely first
                pygame_sim.stop()
                safe_print("[CLEANUP] Pygame simulator stopped")
                
                # make sure pygame is really dead
                import pygame
                try:
                    pygame.display.quit()
                    pygame.quit()
                except:
                    pass
            except Exception as e:
                safe_print(f"[WARNING] Error during pygame cleanup: {e}")
        
        game_engine.cleanup()
        safe_print("[SUCCESS] Game closed successfully")
        safe_print("[DATA] Thanks for playing! Your data has been saved for AI learning.")

if __name__ == "__main__":
    main() 