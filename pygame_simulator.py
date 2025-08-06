import pygame
import sys
import math
import time
from threading import Thread, Lock
from enum import Enum
from config import safe_print

class SimulationState(Enum):
    IDLE = "idle"
    SHOWING_FINGERS = "showing_fingers"
    REACTION = "reaction"
    COUNTDOWN = "countdown"

class PygameSimulator:
    def __init__(self, width=400, height=300, title="Robot Simulation"):
        """Initialize the pygame simulation window"""
        pygame.init()
        
        self.width = width
        self.height = height
        self.title = title
        
        # Create window
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        
        # Colors
        self.colors = {
            'background': (30, 30, 50),
            'robot_body': (100, 100, 150),
            'robot_hand': (200, 180, 160),
            'finger': (220, 200, 180),
            'extended_finger': (255, 220, 200),
            'text': (255, 255, 255),
            'countdown': (255, 255, 0),
            'win': (0, 255, 0),
            'lose': (255, 0, 0),
            'idle': (150, 150, 150)
        }
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Simulation state
        self.state = SimulationState.IDLE
        self.current_fingers = 0
        self.countdown_number = 0
        self.reaction_type = None
        self.animation_time = 0
        self.state_lock = Lock()
        
        # Animation variables
        self.pulse_time = 0
        self.bounce_offset = 0
        
        # Running flag
        self.running = True
        self.clock = pygame.time.Clock()
        
        print("[PYGAME] Pygame robot simulator initialized")
    
    def show_fingers(self, finger_count):
        """Display robot showing specific number of fingers"""
        with self.state_lock:
            self.state = SimulationState.SHOWING_FINGERS
            # Clamp to 1-5 for valid gameplay (0 fingers would be unfair)
            self.current_fingers = max(1, min(5, finger_count))
            self.animation_time = time.time()
            print(f"[ROBOT] Robot simulator showing {self.current_fingers} fingers")
    
    def show_countdown(self, number):
        """Display countdown number"""
        with self.state_lock:
            self.state = SimulationState.COUNTDOWN
            self.countdown_number = number
            print(f"[COUNTDOWN] Robot simulator countdown: {number}")
    
    def show_reaction(self, reaction_type):
        """Display win/lose reaction"""
        with self.state_lock:
            self.state = SimulationState.REACTION
            self.reaction_type = reaction_type
            self.animation_time = time.time()
            safe_print(f"🎭 Robot simulator reaction: {reaction_type}")
    
    def set_idle(self):
        """Set robot to idle state"""
        with self.state_lock:
            self.state = SimulationState.IDLE
            self.current_fingers = 0
            self.countdown_number = 0
            self.reaction_type = None
    
    def draw_robot_base(self, emotion=None, bounce_y=0):
        """Draw a robotic-looking robot with mechanical features"""
        # Robot head (hexagonal for robotic look) with bounce offset
        head_center = (self.width // 2, 80 + bounce_y)
        
        # Draw hexagonal head
        head_points = []
        for i in range(6):
            angle = i * math.pi / 3
            x = head_center[0] + 35 * math.cos(angle)
            y = head_center[1] + 35 * math.sin(angle)
            head_points.append((x, y))
        
        pygame.draw.polygon(self.screen, self.colors['robot_body'], head_points)
        pygame.draw.polygon(self.screen, self.colors['text'], head_points, 3)
        
        # Robot antenna
        antenna_start = (head_center[0], head_center[1] - 35)
        antenna_end = (head_center[0], head_center[1] - 50)
        pygame.draw.line(self.screen, self.colors['text'], antenna_start, antenna_end, 3)
        pygame.draw.circle(self.screen, self.colors['countdown'], antenna_end, 4)
        
        # Robot eyes (LED-style squares)
        left_eye = (head_center[0] - 15, head_center[1] - 8)
        right_eye = (head_center[0] + 15, head_center[1] - 8)
        
        if emotion == 'happy':
            # Happy LED eyes (bright green squares)
            pygame.draw.rect(self.screen, self.colors['win'], 
                           pygame.Rect(left_eye[0] - 6, left_eye[1] - 6, 12, 12))
            pygame.draw.rect(self.screen, self.colors['win'], 
                           pygame.Rect(right_eye[0] - 6, right_eye[1] - 6, 12, 12))
            # Add inner glow
            pygame.draw.rect(self.screen, (255, 255, 255), 
                           pygame.Rect(left_eye[0] - 3, left_eye[1] - 3, 6, 6))
            pygame.draw.rect(self.screen, (255, 255, 255), 
                           pygame.Rect(right_eye[0] - 3, right_eye[1] - 3, 6, 6))
        elif emotion == 'sad':
            # Sad LED eyes (dim red squares)
            pygame.draw.rect(self.screen, self.colors['lose'], 
                           pygame.Rect(left_eye[0] - 6, left_eye[1] - 6, 12, 12))
            pygame.draw.rect(self.screen, self.colors['lose'], 
                           pygame.Rect(right_eye[0] - 6, right_eye[1] - 6, 12, 12))
        else:
            # Normal LED eyes (blue squares)
            pygame.draw.rect(self.screen, (100, 150, 255), 
                           pygame.Rect(left_eye[0] - 6, left_eye[1] - 6, 12, 12))
            pygame.draw.rect(self.screen, (100, 150, 255), 
                           pygame.Rect(right_eye[0] - 6, right_eye[1] - 6, 12, 12))
        
        # Robot mouth (LED strip)
        mouth_y = head_center[1] + 15
        if emotion == 'happy':
            # Smiling LED strip (arc of small rectangles)
            for i in range(7):
                x = head_center[0] - 18 + i * 6
                y = mouth_y - abs(i - 3) * 2  # Arc shape (smiling - curves up)
                pygame.draw.rect(self.screen, self.colors['win'], 
                               pygame.Rect(x - 2, y - 1, 4, 2))
        elif emotion == 'sad':
            # Frowning LED strip
            for i in range(7):
                x = head_center[0] - 18 + i * 6
                y = mouth_y + abs(i - 3) * 2  # Inverted arc (frowning - curves down)
                pygame.draw.rect(self.screen, self.colors['lose'], 
                               pygame.Rect(x - 2, y - 1, 4, 2))
        else:
            # Neutral LED strip (straight line)
            for i in range(7):
                x = head_center[0] - 18 + i * 6
                pygame.draw.rect(self.screen, self.colors['text'], 
                               pygame.Rect(x - 2, mouth_y - 1, 4, 2))
        
        # Robot body (more robotic with panels)
        body_rect = pygame.Rect(self.width // 2 - 30, 120 + bounce_y, 60, 80)
        pygame.draw.rect(self.screen, self.colors['robot_body'], body_rect)
        pygame.draw.rect(self.screen, self.colors['text'], body_rect, 3)
        
        # Add chest panel
        chest_rect = pygame.Rect(self.width // 2 - 20, 130 + bounce_y, 40, 25)
        pygame.draw.rect(self.screen, (80, 80, 120), chest_rect)
        pygame.draw.rect(self.screen, self.colors['text'], chest_rect, 2)
        
        # Add control buttons on chest
        button1 = pygame.Rect(self.width // 2 - 15, 135 + bounce_y, 8, 8)
        button2 = pygame.Rect(self.width // 2 + 7, 135 + bounce_y, 8, 8)
        pygame.draw.rect(self.screen, self.colors['lose'], button1)
        pygame.draw.rect(self.screen, self.colors['win'], button2)
        
        # Return body position for hand connection
        return body_rect
    
    def draw_hand_with_fingers(self, finger_count, center_x, center_y):
        """Draw a modern, minimalistic robotic hand with clear finger count"""
        # Position hand to the right of robot body
        hand_x = center_x + 70
        hand_y = center_y + 10
        
        # Draw robotic arm (clean geometric connection)
        arm_rect = pygame.Rect(center_x + 30, hand_y - 4, 40, 8)
        pygame.draw.rect(self.screen, self.colors['robot_body'], arm_rect)
        pygame.draw.rect(self.screen, self.colors['text'], arm_rect, 2)
        
        # Modern robotic palm (longer rectangle, more hand-like)
        palm_width, palm_height = 50, 35  # Made palm longer vertically for realistic hand proportions
        palm_rect = pygame.Rect(hand_x - palm_width//2, hand_y - palm_height//2, palm_width, palm_height)
        pygame.draw.rect(self.screen, self.colors['robot_body'], palm_rect)
        pygame.draw.rect(self.screen, self.colors['text'], palm_rect, 2)
        
        # Add robotic palm detail (central line for tech look)
        pygame.draw.line(self.screen, self.colors['text'], 
                        (hand_x - palm_width//2 + 5, hand_y), 
                        (hand_x + palm_width//2 - 5, hand_y), 1)
        
        # Define colors for clear visual distinction
        extended_color = (100, 255, 100)  # Bright green for extended
        folded_color = (80, 80, 100)     # Dark gray for folded
        
        # THUMB - Positioned correctly on the side
        thumb_x = hand_x - palm_width//2 - 6
        thumb_y = hand_y - 5  # Position for extended thumb
        thumb_width, thumb_height = 6, 15
        
        if finger_count >= 1:
            # Extended thumb - bright and prominent, extends outward from side
            thumb_rect = pygame.Rect(thumb_x, thumb_y - thumb_height, thumb_width, thumb_height)
            pygame.draw.rect(self.screen, extended_color, thumb_rect)
            pygame.draw.rect(self.screen, self.colors['text'], thumb_rect, 2)
            
            # Add LED indicator for extended state
            pygame.draw.circle(self.screen, (255, 255, 255), 
                             (thumb_x + thumb_width//2, thumb_y - thumb_height + 3), 1)
        else:
            # Folded thumb - positioned upward at top of palm, not to the left
            folded_thumb_x = hand_x - palm_width//4  # Position toward upper left of palm
            folded_thumb_y = hand_y - palm_height//2 - 3  # At the top of palm
            folded_thumb = pygame.Rect(folded_thumb_x - 3, folded_thumb_y, 6, 8)  # Small upward rectangle
            pygame.draw.rect(self.screen, folded_color, folded_thumb)
            pygame.draw.rect(self.screen, self.colors['text'], folded_thumb, 1)
        
        # FOUR FINGERS - Clean row of identical geometric shapes (MADE LONGER)
        finger_width = 6
        finger_extended_height = 35  # Increased from 25 to 35 for longer fingers
        finger_folded_height = 6     # Made shorter when folded for better contrast
        finger_spacing = 10          # Slightly increased spacing
        
        # Start position for fingers (evenly spaced across palm top)
        start_x = hand_x - (3 * finger_spacing) // 2
        fingers_y = hand_y - palm_height//2
        
        for i in range(4):  # Index, Middle, Ring, Pinky
            finger_number = i + 2  # Fingers 2, 3, 4, 5 (thumb is 1)
            finger_x = start_x + i * finger_spacing
            
            if finger_count >= finger_number:
                # Extended finger - tall and bright
                finger_rect = pygame.Rect(finger_x - finger_width//2, 
                                        fingers_y - finger_extended_height, 
                                        finger_width, finger_extended_height)
                pygame.draw.rect(self.screen, extended_color, finger_rect)
                pygame.draw.rect(self.screen, self.colors['text'], finger_rect, 2)
                
                # LED indicator at fingertip
                pygame.draw.circle(self.screen, (255, 255, 255), 
                                 (finger_x, fingers_y - finger_extended_height + 3), 2)
                
                # Robotic joint indicator (horizontal line mid-finger)
                joint_y = fingers_y - finger_extended_height//2
                pygame.draw.line(self.screen, self.colors['text'], 
                               (finger_x - finger_width//2 + 1, joint_y), 
                               (finger_x + finger_width//2 - 1, joint_y), 1)
            else:
                # Folded finger - short and dim
                finger_rect = pygame.Rect(finger_x - finger_width//2, 
                                        fingers_y - finger_folded_height, 
                                        finger_width, finger_folded_height)
                pygame.draw.rect(self.screen, folded_color, finger_rect)
                pygame.draw.rect(self.screen, self.colors['text'], finger_rect, 1)
        
        # Clean design - no extra indicators needed since fingers are clearly visible
    
    def draw_countdown(self):
        """Draw countdown display"""
        if self.countdown_number > 0:
            # Large countdown number
            text = self.font_large.render(str(self.countdown_number), True, self.colors['countdown'])
            text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(text, text_rect)
            
            # Pulsing circle around number
            pulse_radius = 60 + math.sin(self.pulse_time * 8) * 10
            pygame.draw.circle(self.screen, self.colors['countdown'], 
                             (self.width // 2, self.height // 2), int(pulse_radius), 3)
        else:
            # "GO!" message
            text = self.font_large.render("GO!", True, self.colors['win'])
            text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(text, text_rect)
    
    def draw_reaction(self):
        """Draw win/lose reaction with improved emotions"""
        current_time = time.time()
        elapsed = current_time - self.animation_time
        
        if self.reaction_type == 'win':
            # Happy bouncing robot
            bounce_y = math.sin(elapsed * 6) * 15
            
            # Draw robot with happy emotion and bounce
            self.draw_robot_base(emotion='happy', bounce_y=bounce_y)
            
            # Victory text with bounce
            text_bounce = math.sin(elapsed * 8) * 5
            text = self.font_medium.render("VICTORY!", True, self.colors['win'])
            text_rect = text.get_rect(center=(self.width // 2, 240 + text_bounce))
            self.screen.blit(text, text_rect)
            
            # Enhanced confetti effect
            for i in range(15):
                x = (self.width // 2) + math.sin(elapsed * 4 + i) * 120
                y = 30 + (elapsed * 80 + i * 15) % 220
                size = 3 + math.sin(elapsed * 5 + i) * 2
                colors = [self.colors['win'], self.colors['countdown'], (255, 100, 255), (100, 255, 255)]
                color = colors[i % 4]
                pygame.draw.circle(self.screen, color, (int(x), int(y)), int(size))
        
        elif self.reaction_type == 'lose':
            # Sad drooping robot
            droop_y = min(elapsed * 25, 20)
            
            # Draw robot with sad emotion and droop
            self.draw_robot_base(emotion='sad', bounce_y=droop_y)
            
            # Tear drops
            if elapsed > 1:  # Tears appear after 1 second
                head_center = (self.width // 2, 80 + droop_y)
                tear_drop = min((elapsed - 1) * 30, 40)
                left_tear = (head_center[0] - 15, head_center[1] + 20 + tear_drop)
                right_tear = (head_center[0] + 15, head_center[1] + 20 + tear_drop)
                pygame.draw.circle(self.screen, (100, 150, 255), left_tear, 4)
                pygame.draw.circle(self.screen, (100, 150, 255), right_tear, 4)
            
            # Defeat text with droop
            text = self.font_medium.render("DEFEAT...", True, self.colors['lose'])
            text_rect = text.get_rect(center=(self.width // 2, 240 + droop_y))
            self.screen.blit(text, text_rect)
    
    def update(self):
        """Update animation state"""
        self.pulse_time = time.time()
        
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.running = False
                    return False
        
        # Check if we should stop running
        if not self.running:
            return False
        
        # Clear screen
        self.screen.fill(self.colors['background'])
        
        with self.state_lock:
            current_state = self.state
            
            if current_state == SimulationState.IDLE:
                # Draw idle robot
                self.draw_robot_base()
                
                # Idle text
                text = self.font_small.render("Robot Ready", True, self.colors['idle'])
                text_rect = text.get_rect(center=(self.width // 2, 240))
                self.screen.blit(text, text_rect)
            
            elif current_state == SimulationState.COUNTDOWN:
                # Draw countdown
                self.draw_robot_base()
                self.draw_countdown()
            
            elif current_state == SimulationState.SHOWING_FINGERS:
                # Draw robot showing fingers
                body_rect = self.draw_robot_base()
                
                # Draw hand with fingers - connected to body
                hand_center = (body_rect.centerx, body_rect.centery)
                self.draw_hand_with_fingers(self.current_fingers, hand_center[0], hand_center[1])
                
                # Finger count text
                text = self.font_medium.render(f"Showing {self.current_fingers} fingers", 
                                             True, self.colors['text'])
                text_rect = text.get_rect(center=(self.width // 2, 240))
                self.screen.blit(text, text_rect)
            
            elif current_state == SimulationState.REACTION:
                # Draw reaction
                self.draw_reaction()
        
        # Update display
        pygame.display.flip()
        self.clock.tick(60)  # 60 FPS
        return True
    
    def run(self):
        """Main simulation loop (runs in separate thread)"""
        print("[PYGAME] Starting pygame simulation loop")
        try:
            while self.running:
                if not self.update():
                    break
        except Exception as e:
            safe_print(f"🎮 Pygame error: {e}")
        finally:
            try:
                pygame.display.quit()
                pygame.quit()
            except:
                pass
            safe_print("🎮 Pygame simulation closed")
    
    def start_thread(self):
        """Start the simulation in a separate thread"""
        self.simulation_thread = Thread(target=self.run, daemon=True)
        self.simulation_thread.start()
        return self.simulation_thread
    
    def stop(self):
        """Stop the simulation"""
        print("[STOP] Stopping pygame simulator...")
        self.running = False
        
        # Wait for thread to stop naturally first
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=1.0)  # Wait up to 1 second
            
        # Force quit pygame if needed
        try:
            pygame.quit()
        except:
            pass
            
        # If thread is still alive after timeout, terminate forcefully
        if self.simulation_thread and self.simulation_thread.is_alive():
            print("[WARNING] Pygame thread didn't stop gracefully, forcing termination")
            # Note: Python doesn't have thread termination, so we just flag it
            
        print("[STOP] Pygame simulator stopped") 