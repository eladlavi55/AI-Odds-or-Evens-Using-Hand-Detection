import cv2
from config import COLORS, GAME_CONFIG

class UIManager:
    def __init__(self):
        """Set up the UI drawing system"""
        self.font = cv2.FONT_HERSHEY_SIMPLEX
    
    def draw_menu(self, frame, player_choice, player_wins, robot_wins):
        """Draw the main menu screen"""
        height, width = frame.shape[:2]
        
        # darken the background a bit
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, height), COLORS['BLACK'], -1)
        frame = cv2.addWeighted(frame, 0.4, overlay, 0.6, 0)
        
        # game title
        title = "ODDS OR EVENS GAME"
        title_size = cv2.getTextSize(title, self.font, 1.2, 3)[0]
        title_x = (width - title_size[0]) // 2
        cv2.putText(frame, title, (title_x, 80), self.font, 1.2, COLORS['WHITE'], 3)
        
        # help text
        instructions = [
            "Press SPACE to start game",
            "Press 'O' for ODDS, 'E' for EVENS", 
            "Press 'Q' to quit",
            "",
            f"Current choice: {player_choice.upper()}",
            "",
            f"Score - Player: {player_wins} | Robot: {robot_wins}",
            "",
            "River AI is learning your patterns!"
        ]
        
        y_pos = 150
        for instruction in instructions:
            if instruction:  # skip blank lines
                text_size = cv2.getTextSize(instruction, self.font, 0.7, 2)[0]
                text_x = (width - text_size[0]) // 2
                color = COLORS['CYAN'] if "Current choice" in instruction else COLORS['WHITE']
                color = COLORS['GREEN'] if "Score" in instruction else color
                color = COLORS['YELLOW'] if "[ROBOT]" in instruction else color
                cv2.putText(frame, instruction, (text_x, y_pos), self.font, 0.7, color, 2)
            y_pos += 35
        
        return frame
    
    def draw_countdown(self, frame, countdown_number):
        """Draw countdown display"""
        height, width = frame.shape[:2]
        
        if countdown_number > 0:
            text = str(countdown_number)
            color = COLORS['RED']
            scale = 4
        else:
            text = "GO!"
            color = COLORS['GREEN']
            scale = 3
        
        text_size = cv2.getTextSize(text, self.font, scale, 6)[0]
        text_x = (width - text_size[0]) // 2
        text_y = (height + text_size[1]) // 2
        
        cv2.putText(frame, text, (text_x, text_y), self.font, scale, color, 6)
        
        return frame
    
    def draw_game_interface(self, frame, game_state, hand_detector):
        """Draw the main game interface"""
        height, width = frame.shape[:2]
        
        # Round information (Best of 3 format)
        round_text = f"Round {game_state['current_round']}/{GAME_CONFIG['MAX_ROUNDS']} (Best of 3)"
        cv2.putText(frame, round_text, (10, 35), self.font, 0.8, COLORS['WHITE'], 2)
        
        # Player choice
        choice_text = f"You chose: {game_state['player_choice'].upper()}"
        cv2.putText(frame, choice_text, (10, 70), self.font, 0.7, COLORS['CYAN'], 2)
        
        # Current score
        score_text = f"Score - You: {game_state['player_wins']} | Robot: {game_state['robot_wins']}"
        cv2.putText(frame, score_text, (10, 105), self.font, 0.7, COLORS['GREEN'], 2)
        
        # Instructions based on game state
        if game_state.get('waiting_for_next_round', False):
            cv2.putText(frame, "Press O/E to change choice, SPACE for next round", 
                       (10, 140), self.font, 0.6, COLORS['YELLOW'], 2)
            # Add additional visual indication
            cv2.putText(frame, "WAITING FOR NEXT ROUND", 
                       (10, 170), self.font, 0.8, COLORS['CYAN'], 2)
        
        # Exit instruction
        cv2.putText(frame, "Press ESC to exit game", (width - 280, 35), 
                   self.font, 0.6, COLORS['WHITE'], 1)
        
        # Show current numbers if not in countdown
        if not game_state.get('countdown_active', False) and not game_state.get('waiting_for_next_round', False):
            finger_text = f"Your fingers: {game_state['finger_count']}"
            cv2.putText(frame, finger_text, (10, height - 80), self.font, 1.0, COLORS['YELLOW'], 2)
            
            robot_text = f"Robot number: {game_state['robot_number']}"
            cv2.putText(frame, robot_text, (10, height - 40), self.font, 1.0, COLORS['MAGENTA'], 2)
            
            # Debug display - show raw detection
            debug_text = f"DEBUG: Detecting {game_state['finger_count']} fingers"
            cv2.putText(frame, debug_text, (10, height - 120), self.font, 0.6, COLORS['CYAN'], 1)
            
            # Add prediction info
            if 'ai_prediction' in game_state:
                pred = game_state['ai_prediction']
                pred_text = f"AI Predicted: {pred['finger_count']} fingers, {pred['choice'].upper()} ({pred['confidence']:.1%})"
                cv2.putText(frame, pred_text, (10, height - 160), self.font, 0.5, COLORS['MAGENTA'], 1)
            
            # Add finger name indicators in debug mode
            finger_debug_info = hand_detector.get_finger_debug_info()
            for i, finger_status in enumerate(finger_debug_info):
                status_color = COLORS['GREEN'] if "UP" in finger_status else COLORS['RED']
                cv2.putText(frame, finger_status, (width - 150, 80 + i*25), 
                           self.font, 0.5, status_color, 1)
        
        return frame
    
    def draw_round_result(self, frame, game_state):
        """Draw the final result of a round based on stored data."""
        result_data = game_state.get('last_round_data')
        if not result_data:
            return frame  # Don't draw if there's no data

        player_wins_round = result_data.get('player_won_round', False)  # Fixed: was 'player_wins_round'
        player_fingers = result_data.get('player_fingers', 0)
        robot_fingers = result_data.get('robot_fingers', 0)
        total = result_data.get('total', 0)
        
        # Determine result text and color from stored data
        if player_wins_round:
            result_text = "YOU WIN THIS ROUND!"
            result_color = COLORS['GREEN']
        else:
            result_text = "ROBOT WINS THIS ROUND!"
            result_color = COLORS['RED']
            
        # Display the result text - moved lower to avoid overlap
        cv2.putText(frame, result_text, (frame.shape[1] // 2 - 250, frame.shape[0] - 80),
                   cv2.FONT_HERSHEY_TRIPLEX, 1.2, result_color, 3)
                   
        # Display the details of the round
        details_y = frame.shape[0] // 2 - 50
        cv2.putText(frame, f"You: {player_fingers} fingers", (frame.shape[1] // 2 - 150, details_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, COLORS['WHITE'], 2)
        cv2.putText(frame, f"Robot: {robot_fingers}", (frame.shape[1] // 2 - 150, details_y + 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, COLORS['WHITE'], 2)
        cv2.putText(frame, f"Total: {total} ({'ODD' if total % 2 != 0 else 'EVEN'})", 
                   (frame.shape[1] // 2 - 150, details_y + 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, COLORS['WHITE'], 2)
        
        return frame
    
    def draw_final_result(self, frame, player_wins, robot_wins):
        """Draw final game result"""
        height, width = frame.shape[:2]
        
        # Full overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, height), COLORS['BLACK'], -1)
        frame = cv2.addWeighted(frame, 0.3, overlay, 0.7, 0)
        
        # Determine game winner
        if player_wins > robot_wins:
            winner_text = "YOU WIN THE GAME!"
            winner_color = COLORS['GREEN']
        elif robot_wins > player_wins:
            winner_text = "ROBOT WINS THE GAME!"
            winner_color = COLORS['RED']
        else:
            winner_text = "IT'S A TIE!"
            winner_color = COLORS['YELLOW']
        
        # Final result display
        final_lines = [
            "GAME OVER!",
            "",
            f"Final Score:",
            f"Player: {player_wins}",
            f"Robot: {robot_wins}",
            "",
            winner_text,
            "",
            "Press SPACE to play again",
            "Press Q to quit"
        ]
        
        y_start = 100
        for i, line in enumerate(final_lines):
            if line:
                text_size = cv2.getTextSize(line, self.font, 0.8, 2)[0]
                text_x = (width - text_size[0]) // 2
                
                if "GAME OVER" in line:
                    color = COLORS['WHITE']
                    scale = 1.2
                elif "WIN" in line or "TIE" in line:
                    color = winner_color
                    scale = 1.0
                else:
                    color = COLORS['WHITE']
                    scale = 0.8
                
                cv2.putText(frame, line, (text_x, y_start + i * 35), self.font, scale, color, 2)
        
        return frame
    
    def draw_ai_status(self, frame, ai_predictor):
        """Draw AI learning status on frame"""
        height, width = frame.shape[:2]
        
        # AI status info
        stats = ai_predictor.player_stats
        total_games = stats['total_games']
        total_rounds = stats['total_rounds']
        
        if total_rounds > 0:
            status_text = f"AI: {total_rounds} rounds learned | Accuracy improving"
            color = COLORS['GREEN'] if total_rounds > 10 else COLORS['YELLOW']
        else:
            status_text = "AI: Learning your patterns..."
            color = COLORS['CYAN']
        
        cv2.putText(frame, status_text, (10, height - 200), self.font, 0.5, color, 1)
        
        return frame 