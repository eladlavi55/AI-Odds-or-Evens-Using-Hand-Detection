import cv2
import mediapipe as mp
from config import GAME_CONFIG

class HandDetector:
    def __init__(self):
        """Set up MediaPipe for hand detection"""
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=GAME_CONFIG['MIN_DETECTION_CONFIDENCE'],
            min_tracking_confidence=GAME_CONFIG['MIN_TRACKING_CONFIDENCE']
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.last_debug_fingers = [False, False, False, False, False]
        
    def detect_hands(self, frame):
        """Look for hands in the camera image"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        return results
    
    def draw_landmarks(self, frame, hand_landmarks):
        """Draw the hand skeleton on the image"""
        self.mp_drawing.draw_landmarks(
            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
    
    def count_fingers(self, landmarks):
        """Figure out how many fingers are up
        Based on MediaPipe finger counting techniques
        """
        count = 0
        fingers_status = [False, False, False, False, False]  # which fingers are up
        
        # figure out if it's left or right hand
        # (camera mirror-flips everything)
        is_right_hand = landmarks[17].x < landmarks[5].x
        hand_type = "Right" if is_right_hand else "Left"
        print(f"Detected {hand_type} hand")
        
        # check thumb - it's tricky because left/right hand are different
        if (hand_type == "Right" and landmarks[4].x > landmarks[3].x) or \
           (hand_type == "Left" and landmarks[4].x < landmarks[3].x):
            count += 1
            fingers_status[0] = True
            print(f"Thumb UP ({hand_type} hand)")
        else:
            print(f"Thumb DOWN ({hand_type} hand)")
        
        # other fingers are easy - just check if tip is above the knuckle
        
        # pointer finger
        if landmarks[8].y < landmarks[6].y:
            count += 1
            fingers_status[1] = True
            print("Index UP")
        else:
            print("Index DOWN")
        
        # Middle finger
        if landmarks[12].y < landmarks[10].y:
            count += 1
            fingers_status[2] = True
            print("Middle UP")
        else:
            print("Middle DOWN")
        
        # Ring finger
        if landmarks[16].y < landmarks[14].y:
            count += 1
            fingers_status[3] = True
            print("Ring UP")
        else:
            print("Ring DOWN")
        
        # Pinky finger
        if landmarks[20].y < landmarks[18].y:
            count += 1
            fingers_status[4] = True
            print("Pinky UP")
        else:
            print("Pinky DOWN")
        
        print(f"Total fingers detected: {count}")
        
        # save this for debugging
        self.last_debug_fingers = fingers_status
        
        # no cheating with 0 fingers! force at least 1
        if count == 0:
            print("ZERO fingers detected - forcing to 1 for fair gameplay")
            count = 1
        
        # should be 1-5 now
        return count
    
    def get_finger_debug_info(self):
        """Return finger status for debugging"""
        finger_names = ["THUMB", "INDEX", "MIDDLE", "RING", "PINKY"]
        debug_info = []
        for i, up in enumerate(self.last_debug_fingers):
            status = "UP" if up else "DOWN"
            debug_info.append(f"{finger_names[i]}: {status}")
        return debug_info 