import cv2
import random
import time
from threading import Thread
from datetime import datetime
import os
import numpy as np

from config import GAME_CONFIG, VIDEO_DIR, VIDEO_PATHS, safe_print
from hand_detector import HandDetector
from video_manager import VideoManager
from ai_predictor import AIPredictor
from ui_manager import UIManager
from arduino_controller import ArduinoController, find_arduino_port

class GameEngine:
    def __init__(self):
        """Set up the game engine and all its parts"""
        print("[INIT] Initializing Game Engine...")
        
        # keep track of the current game state
        self.game_active = False
        self.game_over = False
        self.current_round = 0
        self.max_rounds = 3
        self.player_wins = 0
        self.robot_wins = 0
        
        # stuff for managing individual rounds
        self.countdown_active = False
        self.countdown_number = 0
        self.finger_detection_phase = False  # when we're waiting for player to show fingers
        self.show_result = False
        self.waiting_for_next_round = False
        self.round_ended = False
        
        # current round data
        self.finger_count = 0
        self.robot_number = 0
        self.player_choice = "odds"  # player starts with odds
        self.ai_prediction = None
        self.last_round_data = None
        
        # create all the main components
        self.hand_detector = HandDetector()
        self.video_manager = VideoManager()
        self.ai_predictor = AIPredictor()
        self.ui_manager = UIManager()
        
        # make sure we have all the video files we need
        self._ensure_videos_exist()
        
        # try to connect to Arduino for LED effects
        print("[HARDWARE] Initializing Arduino controller...")
        self.arduino = None
        
        # auto-detect Arduino port
        arduino_port = find_arduino_port()
        if arduino_port:
            print(f"[ARDUINO] Found Arduino port: {arduino_port}")
            try:
                self.arduino = ArduinoController(port=arduino_port)
                if not self.arduino.is_connected():
                    safe_print(f"❌ Failed to connect to Arduino on {arduino_port}")
                    self.arduino = None
            except Exception as e:
                safe_print(f"❌ Error initializing Arduino on {arduino_port}: {e}")
                self.arduino = None
        
        # if that didn't work, try the usual Windows COM ports
        if not self.arduino:
            print("[ARDUINO] Trying common Windows ports...")
            for port in ['COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8']:
                try:
                    print(f"   Trying {port}...")
                    test_arduino = ArduinoController(port=port)
                    if test_arduino.is_connected():
                        self.arduino = test_arduino
                        print(f"[ARDUINO] Connected to Arduino on {port}")
                        break
                    else:
                        test_arduino.disconnect()
                except Exception as e:
                    print(f"   {port} failed: {e}")
                    continue
        
        # if Arduino is working, set up button handling
        if self.arduino and self.arduino.is_connected():
            self.arduino.set_button_callback(self._arduino_button_pressed)
            print("[ARDUINO] Arduino controller ready! Use the button as spacebar.")
            print("[ARDUINO] LEDs will light up during countdown")
            
            # show a startup message on the LCD
            print("[ARDUINO] Showing initial game start message...")
            self.arduino.show_game_start_message()
            time.sleep(0.5)
        else:
            print("[WARNING] Arduino not connected - game will work without physical controls")
            print("[INFO] Make sure Arduino is connected and try restarting the game")
            self.arduino = None
        
        # pygame window for robot simulation
        self.pygame_simulator = None
        
        print("Game engine initialized with AI learning capabilities!")
    
    def _arduino_button_pressed(self):
        """Arduino button was pressed - treat it like spacebar"""
        safe_print("🔘 Arduino button pressed!")
        # just pretend they hit spacebar
        self.handle_keypress(ord(' '))
    
    def set_pygame_simulator(self, pygame_sim):
        """Connect the pygame window to this game engine"""
        self.pygame_simulator = pygame_sim
        print("[PYGAME] Pygame simulator connected to game engine")
    
    def get_game_state(self):
        """Return all the current game info in a dict"""
        return {
            'game_active': self.game_active,
            'current_round': self.current_round,
            'max_rounds': self.max_rounds,
            'player_wins': self.player_wins,
            'robot_wins': self.robot_wins,
            'countdown_active': self.countdown_active,
            'countdown_number': self.countdown_number,
            'show_result': self.show_result,
            'waiting_for_next_round': self.waiting_for_next_round,
            'finger_count': self.finger_count,
            'robot_number': self.robot_number,
            'player_choice': self.player_choice,
            'ai_prediction': self.ai_prediction,
            'last_round_data': self.last_round_data
        }
    
    def start_countdown_sequence(self):
        """Begin the 3-2-1-GO countdown"""
        self.countdown_active = True
        
        # ask the AI what it thinks the player will do
        try:
            game_state = self.get_game_state()
            self.ai_prediction = self.ai_predictor.predict_player_behavior(game_state)
            
            # use AI's guess to pick robot's move
            predicted_fingers = self.ai_prediction['finger_count']
            predicted_choice = self.ai_prediction['choice']
            
            # let AI decide what robot should show
            ai_robot_number = self.ai_predictor.get_robot_strategy(predicted_fingers, predicted_choice)
            
            print(f"[AI] Strategy: Predicted you'll show {predicted_fingers} fingers and choose {predicted_choice}")
            print(f"[AI] Robot will show {ai_robot_number} fingers")
            
        except Exception as e:
            print(f"AI prediction error: {e}")
            ai_robot_number = 3  # Safe default
            self.ai_prediction = {'finger_count': 3, 'choice': 'odds', 'confidence': 0.0}
        
        # robot can show 1-5 fingers (no cheating with 0!)
        valid_numbers = [1, 2, 3, 4, 5]
        if ai_robot_number in valid_numbers:
            smart_robot_number = ai_robot_number
        else:
            # if AI picks something weird, just go random
            smart_robot_number = random.choice(valid_numbers)
        
        # remember what the robot picked
        self.robot_number = smart_robot_number
        
        print(f"[ROBOT] Will show {smart_robot_number} fingers (guaranteed valid, parity: {'odd' if smart_robot_number % 2 == 1 else 'even'})")
        
        countdown_thread = Thread(target=self.run_countdown, args=(smart_robot_number,))
        countdown_thread.daemon = True
        countdown_thread.start()
    
    def run_countdown(self, smart_robot_number):
        """Do the actual countdown (runs in separate thread)"""
        try:
            print("[COUNTDOWN] Starting countdown sequence...")
            print(f"[ROBOT] Will show {smart_robot_number} fingers (parity: {'odd' if smart_robot_number % 2 == 1 else 'even'})")
            
            # Check if game was ended while countdown was starting
            if self.game_over:
                print("[WARNING] Game was ended during countdown setup - aborting countdown")
                self.countdown_active = False
                return
            
            # Robot number is already set in start_countdown_sequence
            # Just verify it's correct
            if self.robot_number != smart_robot_number:
                print(f"[WARNING] Robot number mismatch! Fixing: {self.robot_number} -> {smart_robot_number}")
                self.robot_number = smart_robot_number
            
            # Show between-rounds message on Arduino (only for rounds 2 and 3, not the first round)
            if self.current_round > 1:
                if self.arduino and self.arduino.is_connected():
                    print("[ARDUINO] Showing between-rounds message...")
                    self.arduino.show_between_rounds_message()
                    time.sleep(0.2)
                else:
                    print("[WARNING] No Arduino connected for between-rounds message")
            else:
                print("[INFO] First round - game start message already shown")
            
            # Countdown 3, 2, 1
            for i in range(3, 0, -1):
                print(f"[COUNTDOWN] {i}")
                self.countdown_number = i
                
                # Update pygame simulator
                if self.pygame_simulator:
                    self.pygame_simulator.show_countdown(i)
                
                # Trigger Arduino countdown effects
                if self.arduino and self.arduino.is_connected():
                    print(f"[ARDUINO] Sending command for countdown {i}")
                    if i == 3:
                        success = self.arduino.countdown_3()
                        print(f"   Red LED command sent: {success}")
                    elif i == 2:
                        success = self.arduino.countdown_2()
                        print(f"   Yellow LED command sent: {success}")
                    elif i == 1:
                        success = self.arduino.countdown_1()
                        print(f"   Green LED command sent: {success}")
                else:
                    print(f"[WARNING] Arduino not available for countdown {i}")
                
                time.sleep(1)
            
            # Show GO!
            print("[COUNTDOWN] GO!")
            self.countdown_number = 0
            
            # Update pygame simulator for GO
            if self.pygame_simulator:
                self.pygame_simulator.show_countdown(0)  # 0 means "GO!"
            
            # Trigger Arduino GO effect
            if self.arduino and self.arduino.is_connected():
                print("[ARDUINO] Sending GO command")
                success = self.arduino.countdown_go()
                print(f"   GO command sent: {success}")
            else:
                print("[WARNING] Arduino not available for GO effect")
            
            time.sleep(1)
            
            # Set robot number (using AI strategy)
            self.robot_number = smart_robot_number
            print(f"[ROBOT] Shows {self.robot_number} fingers")
            
            # Update pygame simulator to show fingers
            if self.pygame_simulator:
                self.pygame_simulator.show_fingers(self.robot_number)
            
            # Play robot finger video
            try:
                self.video_manager.play_robot_finger_video(self.robot_number)
            except Exception as e:
                safe_print(f"❌ Error playing robot finger video: {e}")
            
            # CRITICAL: Let the main thread know the countdown is done
            self.countdown_active = False
            
            # Enter finger detection phase
            self.finger_detection_phase = True
            safe_print("👋 Show your fingers now!")
            time.sleep(2)  # Give player 2 seconds to show fingers
            
            # Exit finger detection phase and signal result processing
            self.finger_detection_phase = False
            self.round_ended = True  # Signal main loop to process the result
            
        except Exception as e:
            safe_print(f"❌ Error in countdown sequence: {e}")
            # Make sure we exit countdown mode even if there's an error
            self.countdown_active = False
            self.finger_detection_phase = False
            self.round_ended = True  # Signal main loop to process the result
    
    def _process_round_result(self):
        """Process the round result (called from main update loop)"""
        print(f"[ROUND] Processing end of round {self.current_round}")
        print(f"[DEBUG] Player finger count detected: {self.finger_count}")
        print(f"[DEBUG] Robot finger count: {self.robot_number}")
        
        total = self.finger_count + self.robot_number
        is_odd = total % 2 == 1
        player_chose_odds = (self.player_choice == "odds")
        player_wins_round = (is_odd and player_chose_odds) or (not is_odd and not player_chose_odds)
        
        if player_wins_round:
            self.player_wins += 1
            print(f"[RESULT] Player wins round {self.current_round}!")
            # Show player round win message on Arduino
            if self.arduino and self.arduino.is_connected():
                self.arduino.show_player_round_win_message()
        else:
            self.robot_wins += 1
            print(f"[RESULT] Robot wins round {self.current_round}!")
            # Show robot round win message on Arduino
            if self.arduino and self.arduino.is_connected():
                self.arduino.show_robot_round_win_message()
            
        print(f"[SCORE] Player {self.player_wins} - Robot {self.robot_wins}")
        
        # Check for game completion first
        is_game_over = self.player_wins >= 2 or self.robot_wins >= 2
        if is_game_over:
            self.game_over = True
            print("[GAME] FINISHED! First to 2 wins achieved.")

        # Create the complete, definitive data packet for this round
        round_data = {
            'timestamp': datetime.now().isoformat(),
            'current_round': self.current_round,
            'player_fingers': self.finger_count,
            'robot_fingers': self.robot_number,
            'player_choice': self.player_choice,
            'total': total,
            'is_odd': is_odd,
            'player_won_round': player_wins_round,
            'player_wins': self.player_wins,
            'robot_wins': self.robot_wins,
            'ai_prediction': self.ai_prediction,
            'game_finished': is_game_over
        }
        
        # Store this data for the UI to use
        self.last_round_data = round_data
        
        # Update AI model with the complete data packet
        self.ai_predictor.update_model(round_data)
        self.ai_predictor.save_data()
        
        # Show the robot's fingers in pygame simulator
        if self.pygame_simulator:
            self.pygame_simulator.show_fingers(self.robot_number)
        
        # DELAY showing the result - show player and robot choices first
        # This gives players time to see what both chose before showing win/lose
        self.show_result = True
        self.waiting_for_next_round = True
        
        # Now, handle the game state transition with delay
        def delayed_reaction():
            try:
                # Wait 3 seconds to let players see the choices
                time.sleep(3)
                
                if is_game_over:
                    # Game is over - show final result with videos
                    self.game_active = False # Stop the active game
                    
                    self.video_manager.stop_video()
                    time.sleep(0.2)
                    
                    if self.player_wins > self.robot_wins:
                        print("[VIDEO] Playing robot 'lose' video for game end...")
                        self.video_manager.play_robot_reaction_video('lose')
                        if self.pygame_simulator:
                            self.pygame_simulator.show_reaction('lose')
                        if self.arduino: self.arduino.player_wins()
                    else:
                        print("[VIDEO] Playing robot 'win' video for game end...")
                        self.video_manager.play_robot_reaction_video('win')
                        if self.pygame_simulator:
                            self.pygame_simulator.show_reaction('win')
                        if self.arduino: self.arduino.player_loses()
                    
                    print("Press SPACE to see final score.")
                else:
                    # Regular round end - just show reaction in simulator without videos
                    if player_wins_round:
                        if self.pygame_simulator:
                            self.pygame_simulator.show_reaction('lose')
                        # Don't play video for regular rounds
                        print(f"Round {self.current_round} complete. Press SPACE to continue.")
                    else:
                        if self.pygame_simulator:
                            self.pygame_simulator.show_reaction('win')
                        # Don't play video for regular rounds
                        print(f"Round {self.current_round} complete. Press SPACE to continue.")
                
                # Ensure we're in the right state to continue
                self.waiting_for_next_round = True
            except Exception as e:
                safe_print(f"❌ Error in delayed_reaction: {e}")
        
        # Start the delay timer in a separate thread
        delay_thread = Thread(target=delayed_reaction)
        delay_thread.daemon = True
        delay_thread.start()
        
        if self.game_over:
            print("Press SPACE to see final score.")
    
    def reset_game(self):
        """Reset game state for a new game"""
        print("[RESET] Resetting game state completely")
        self.video_manager.stop_video()
        self.game_active = False
        self.game_over = False
        self.current_round = 0
        self.player_wins = 0
        self.robot_wins = 0
        self.countdown_active = False
        self.finger_detection_phase = False
        self.show_result = False
        self.waiting_for_next_round = False
        self.finger_count = 0
        self.robot_number = 0
        self.ai_prediction = None
        self.last_round_data = None
        self.round_ended = False
        
        # Reset pygame simulator to idle
        if self.pygame_simulator:
            self.pygame_simulator.set_idle()
        
        if self.arduino and self.arduino.is_connected():
            self.arduino.show_game_start_message()
        print("[RESET] Game reset complete - ready for new game")
    
    def update(self):
        """Update game state, called every frame from the main loop."""
        if self.round_ended:
            # The countdown has finished, process the result now in the main thread
            self.round_ended = False  # Consume the flag to ensure it only runs once
            self._process_round_result()
    
    def process_frame(self, frame):
        """Process a single frame and return the rendered frame"""
        # First, update the game state machine
        self.update()
        
        # Detect hands and count fingers
        results = self.hand_detector.detect_hands(frame)
        
        # Process hand landmarks and count fingers
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                self.hand_detector.draw_landmarks(frame, hand_landmarks)
                
                # Count fingers when game is active OR during finger detection phase
                if self.game_active and (not self.show_result or self.finger_detection_phase):
                    detected_count = self.hand_detector.count_fingers(hand_landmarks.landmark)
                    self.finger_count = detected_count
                    
                    if self.finger_detection_phase:
                        safe_print(f"👋 Detecting fingers during detection phase: {detected_count}")
        
        # Draw appropriate interface based on game state
        game_state = self.get_game_state()
        
        if not self.game_active:
            if self.current_round > 0:  # Game was played and finished
                # Game finished - show final results
                frame = self.ui_manager.draw_final_result(frame, self.player_wins, self.robot_wins)
            else:
                # Show main menu
                frame = self.ui_manager.draw_menu(frame, self.player_choice, 
                                                self.player_wins, self.robot_wins)
        else:
            # Game is active
            frame = self.ui_manager.draw_game_interface(frame, game_state, self.hand_detector)
            
            if self.countdown_active:
                # Show countdown
                frame = self.ui_manager.draw_countdown(frame, self.countdown_number)
            elif self.finger_detection_phase:
                # Show finger detection prompt
                cv2.putText(frame, "SHOW YOUR FINGERS NOW!", 
                          (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, f"Detected: {self.finger_count} fingers", 
                          (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            elif self.show_result:
                # Show round result
                frame = self.ui_manager.draw_round_result(frame, game_state)
        
        # Draw AI status
        frame = self.ui_manager.draw_ai_status(frame, self.ai_predictor)
        
        # Apply video overlay if video is playing
        frame = self.video_manager.overlay_video_on_frame(frame)
        
        return frame
    
    def handle_keypress(self, key):
        """Handle keyboard input based on a clear state machine"""
        print(f"[INPUT] Key pressed: {chr(key) if 32 <= key <= 126 else key}, Waiting: {self.waiting_for_next_round}, Game Over: {self.game_over}")
        
        if key == ord('q'):
            return 'quit'
        elif key == 27:  # ESC key to reset to main menu
            self.reset_game()
            return 'continue'

        if key == ord(' '):  # Spacebar logic
            # Case 1: Game is over, SPACE resets to main menu
            if self.game_over:
                print("[GAME] Game over - resetting to main menu")
                self.reset_game()
                return 'continue'

            # Case 2: Not in a game, SPACE starts a new one
            if not self.game_active:
                print("[GAME] Starting new game")
                self.reset_game()
                self.game_active = True
                self.current_round = 1
                self.start_countdown_sequence()
                return 'continue'
            
            # Case 3: In a game, waiting for next round, SPACE starts it
            if self.waiting_for_next_round:
                print(f"[GAME] Starting round {self.current_round + 1}")
                self.waiting_for_next_round = False
                self.show_result = False
                self.current_round += 1
                self.start_countdown_sequence()
                return 'continue'

        # Handle O/E for choosing odds/evens only when not in an active countdown
        if not self.countdown_active and not self.finger_detection_phase:
            if key == ord('o') or key == ord('O'):
                self.player_choice = "odds"
                print("[PLAYER] Player chose: ODDS")
            elif key == ord('e') or key == ord('E'):
                self.player_choice = "evens"
                print("[PLAYER] Player chose: EVENS")

        return 'continue'
    
    def _play_robot_video(self, reaction_type):
        """Play the appropriate robot reaction video"""
        try:
            if reaction_type == 'win':
                print("[VIDEO] Playing robot 'win' video...")
                self.video_manager.play_robot_reaction_video('win')
                if self.arduino: 
                    self.arduino.player_loses()
            elif reaction_type == 'lose':
                print("[VIDEO] Playing robot 'lose' video...")
                self.video_manager.play_robot_reaction_video('lose')
                if self.arduino: 
                    self.arduino.player_wins()
        except Exception as e:
            safe_print(f"❌ Error playing robot {reaction_type} video: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        self.video_manager.stop_video()
        self.ai_predictor.save_data()
        
        # Stop pygame simulator
        if self.pygame_simulator:
            self.pygame_simulator.stop()
        
        # Disconnect Arduino
        if self.arduino and self.arduino.is_connected():
            self.arduino.disconnect()
        
        print("[CLEANUP] Game engine cleanup complete")
    
    def _ensure_videos_exist(self):
        """Check for all required videos and create placeholders if missing."""
        print("[VIDEO] Checking for required video files...")
        all_videos_ok = True
        
        # Add a check for the base video path dictionary
        if 'robot_fingers' not in VIDEO_PATHS or 'robot_reactions' not in VIDEO_PATHS:
             safe_print("❌ FATAL: VIDEO_PATHS dictionary in config.py is malformed.")
             return # Or raise an exception
        
        # Check finger videos for 1, 2, 3, 4, 5 (all possible finger counts)
        for i in [1, 2, 3, 4, 5]:
            path = VIDEO_PATHS['robot_fingers'].get(i)
            # Make the check more robust against None paths
            if not path or not os.path.exists(path):
                all_videos_ok = False
                # Ensure path is not None before trying to create it
                if path:
                    safe_print(f"⚠️  Missing video: {path}. A placeholder will be created.")
                    self._create_placeholder_video(path, f"Robot {i} Fingers")
                else:
                    print(f"[WARNING] Missing video path configuration for robot finger {i}.")

        # Check reaction videos
        for reaction in ['win', 'lose']:
            path = VIDEO_PATHS['robot_reactions'].get(reaction)
            if not path or not os.path.exists(path):
                all_videos_ok = False
                if path:
                    safe_print(f"⚠️  Missing video: {path}. A placeholder will be created.")
                    self._create_placeholder_video(path, f"Robot {reaction.upper()}S")
                else:
                     print(f"[WARNING] Missing video path configuration for reaction '{reaction}'.")
        
        if all_videos_ok:
            print("[VIDEO] All required videos are available")
        else:
            print("[VIDEO] Placeholders created for missing videos.")
    
    def _create_placeholder_video(self, video_path, text):
        """Create a simple placeholder video file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(video_path), exist_ok=True)
            
            # Create a colored frame
            width, height = 400, 300
            color = (0, 0, 255)  # Red (BGR format)
            if 'win' in video_path.lower():
                color = (0, 255, 0)  # Green
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use mp4v codec
            out = cv2.VideoWriter(video_path, fourcc, 30.0, (width, height))
            
            if not out.isOpened():
                safe_print(f"❌ Failed to create video writer for {video_path}")
                return
            
            # Create 60 frames (2 seconds at 30fps)
            for i in range(60):
                # Create frame
                frame = np.full((height, width, 3), color, dtype=np.uint8)
                
                # Add text
                cv2.putText(frame, text, (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
                cv2.putText(frame, f"Frame {i+1}/60", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Write frame
                out.write(frame)
            
            # Release video writer
            out.release()
            print(f"Created placeholder video: {video_path}")
            
        except Exception as e:
            safe_print(f"❌ Error creating placeholder video: {e}") 