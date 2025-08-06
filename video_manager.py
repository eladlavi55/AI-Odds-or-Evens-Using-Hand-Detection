import cv2
import os
import numpy as np
import threading
import time
from config import VIDEO_PATHS, GAME_CONFIG

class VideoManager:
    def __init__(self):
        """Set up video playback system"""
        self.current_video = None
        self.video_cap = None
        self.video_playing = False
        self.video_thread = None
        self.stop_video_flag = False
        self.current_frame = None
        self.video_start_time = None
        self.video_type = None  # Track if it's 'finger' or 'reaction' video
        
    def play_robot_finger_video(self, finger_count):
        """Show the robot displaying fingers"""
        try:
            video_path = VIDEO_PATHS['robot_fingers'].get(finger_count)
            if video_path and os.path.exists(video_path):
                self._start_video(video_path, video_type='finger')
                print(f"Playing robot {finger_count} finger video")
            else:
                print(f"Robot {finger_count} finger video not found: {video_path}")
                # Create a simple placeholder if video doesn't exist
                self._create_simple_placeholder(finger_count, 'finger')
        except Exception as e:
            print(f"Error playing robot finger video: {e}")
    
    def play_robot_reaction_video(self, reaction):
        """Show robot winning or losing reaction"""
        try:
            video_path = VIDEO_PATHS['robot_reactions'].get(reaction)
            if video_path and os.path.exists(video_path):
                self._start_video(video_path, video_type='reaction')
                print(f"Playing robot {reaction} video to completion")
            else:
                print(f"Robot {reaction} video not found: {video_path}")
                # Create a simple placeholder if video doesn't exist
                self._create_simple_placeholder(reaction, 'reaction')
        except Exception as e:
            print(f"Error playing robot reaction video: {e}")
    
    def _start_video(self, video_path, video_type='finger'):
        """Begin playing video on top of camera feed"""
        # stop whatever video might be playing
        self.stop_video()
        
        self.current_video = video_path
        self.video_type = video_type
        self.video_playing = True
        self.stop_video_flag = False
        self.video_start_time = time.time()
        
        print(f"Started {video_type} video overlay: {os.path.basename(video_path)}")
        
        # play video in background so it doesn't block the game
        self.video_thread = threading.Thread(target=self._video_playback_loop, args=(video_path, video_type))
        self.video_thread.daemon = True
        self.video_thread.start()
    
    def _video_playback_loop(self, video_path, video_type):
        """Load video frames for overlay display"""
        try:
            self.video_cap = cv2.VideoCapture(video_path)
            if not self.video_cap.isOpened():
                print(f"Failed to open video: {video_path}")
                return

            # Get video properties
            fps = self.video_cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if fps > 0:
                frame_duration = 1.0 / fps
                video_duration = total_frames / fps
                print(f"Video info: {total_frames} frames, {fps:.1f} FPS, {video_duration:.1f}s duration")
            else:
                # Fallback to 30 FPS if FPS not available
                frame_duration = 1.0 / 30
                video_duration = total_frames / 30

            frame_count = 0
            loops_played = 0
            max_loops = 1  # Play video once
            
            while self.video_playing and not self.stop_video_flag:
                ret, frame = self.video_cap.read()
                if not ret:
                    # Video ended
                    loops_played += 1
                    if loops_played >= max_loops:
                        print(f"{video_type.title()} video completed ({loops_played} loop{'s' if loops_played != 1 else ''})")
                        break
                    else:
                        # Loop the video
                        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = self.video_cap.read()
                        if not ret:
                            break
                
                # Resize frame for overlay
                frame = cv2.resize(frame, (GAME_CONFIG['VIDEO_DISPLAY_WIDTH'], 
                                         GAME_CONFIG['VIDEO_DISPLAY_HEIGHT']))
                
                # Store current frame for overlay
                self.current_frame = frame.copy()
                
                # Wait for next frame time
                time.sleep(frame_duration)
                frame_count += 1
                
                # Different behavior for different video types
                if video_type == 'finger':
                    # Finger videos: limit to 4 seconds max
                    if frame_count > fps * 4:
                        print("Finger video time limit reached (4s)")
                        break
                elif video_type == 'reaction':
                    # Reaction videos: play to completion (no time limit)
                    # They will naturally end when the video file ends
                    pass
            
            self._cleanup_video()
            
        except Exception as e:
            print(f"Video playback error: {e}")
            self._cleanup_video()
    
    def _cleanup_video(self):
        """Clean up video resources"""
        self.video_playing = False
        self.stop_video_flag = True
        self.current_frame = None
        self.video_type = None
        
        if self.video_cap:
            self.video_cap.release()
            self.video_cap = None
        
        self.current_video = None
        print("Video overlay stopped")
    
    def stop_video(self):
        """Stop current video playback"""
        if self.video_playing:
            print("Stopping video overlay...")
            self.stop_video_flag = True
            self.video_playing = False
            
            # Wait for video thread to finish
            if self.video_thread and self.video_thread.is_alive():
                self.video_thread.join(timeout=1)
            
            self._cleanup_video()
    
    def update_video_frame(self):
        """This method is now handled by the video thread"""
        pass
    
    def overlay_video_on_frame(self, main_frame):
        """Overlay current video frame on the main game frame"""
        if self.current_frame is not None and self.video_playing:
            # Get overlay position
            x = GAME_CONFIG['VIDEO_POSITION_X']
            y = GAME_CONFIG['VIDEO_POSITION_Y']
            h, w = self.current_frame.shape[:2]
            
            # Make sure overlay fits within frame bounds
            frame_h, frame_w = main_frame.shape[:2]
            if x + w <= frame_w and y + h <= frame_h:
                # Add semi-transparent border around video
                border_thickness = 3
                cv2.rectangle(main_frame, 
                            (x - border_thickness, y - border_thickness),
                            (x + w + border_thickness, y + h + border_thickness),
                            (0, 255, 255), border_thickness)
                
                # Overlay the video frame
                main_frame[y:y+h, x:x+w] = self.current_frame
                
                # Add video title
                if self.current_video:
                    video_name = os.path.basename(self.current_video).replace('.mp4', '').replace('_', ' ').title()
                    cv2.putText(main_frame, video_name, (x, y - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        return main_frame
    
    def is_playing(self):
        """Check if video is currently playing"""
        return self.video_playing 
    
    def _create_simple_placeholder(self, identifier, video_type):
        """Create a simple colored placeholder frame instead of video"""
        try:
            # Create a simple colored frame as placeholder
            if video_type == 'finger':
                # Different colors for different finger counts
                colors = {1: (0, 0, 255), 2: (0, 255, 0), 3: (255, 0, 0), 
                         4: (0, 255, 255), 5: (255, 0, 255)}
                color = colors.get(identifier, (128, 128, 128))
                text = f"Robot: {identifier} Finger{'s' if identifier != 1 else ''}"
            else:
                # Win/lose colors
                color = (0, 255, 0) if identifier == 'win' else (0, 0, 255)
                text = f"Robot {identifier.title()}s!"
            
            # Create placeholder frame
            placeholder = np.full((GAME_CONFIG['VIDEO_DISPLAY_HEIGHT'], 
                                 GAME_CONFIG['VIDEO_DISPLAY_WIDTH'], 3), 
                                color, dtype=np.uint8)
            
            # Add text
            cv2.putText(placeholder, text, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, (255, 255, 255), 2)
            cv2.putText(placeholder, "Video Missing", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, (200, 200, 200), 1)
            
            # Set as current frame for a few seconds
            self.current_frame = placeholder
            self.video_playing = True
            
            # Auto-stop after 2 seconds
            def stop_placeholder():
                time.sleep(2)
                self.video_playing = False
                self.current_frame = None
                print("Placeholder video stopped")
            
            placeholder_thread = threading.Thread(target=stop_placeholder)
            placeholder_thread.daemon = True
            placeholder_thread.start()
            
            print(f"Created placeholder for {video_type}: {identifier}")
            
        except Exception as e:
            print(f"Error creating placeholder: {e}") 