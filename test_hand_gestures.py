#!/usr/bin/env python3
"""
Test script for realistic hand gestures
=======================================

This script demonstrates the improved hand gestures with:
- Proper thumb positioning
- 4 fingers (index, middle, ring, pinky)
- Realistic finger counting (1=thumb, 2=thumb+index, etc.)
- Enhanced emotions (happy/sad faces with tears/cheeks)

Press 1-5 to test different finger counts
Press W/L to test win/lose emotions
Press Q to quit
"""

import pygame
import time
from pygame_simulator import PygameSimulator

def main():
    print("[TEST] Testing Realistic Hand Gestures")
    print("=" * 40)
    print("Controls:")
    print("- 1: Thumb only")
    print("- 2: Thumb + Index")
    print("- 3: Thumb + Index + Middle")
    print("- 4: Thumb + Index + Middle + Ring")
    print("- 5: All fingers (full hand)")
    print("- W: Happy robot (win)")
    print("- L: Sad robot (lose)")
    print("- Q: Quit")
    print("=" * 40)
    
    # Create simulator
    simulator = PygameSimulator(
        width=400,
        height=300,
        title="Hand Gesture Test"
    )
    
    # Start in a separate thread
    simulator.start_thread()
    
    # Start with showing 3 fingers
    simulator.show_fingers(3)
    
    # Test loop
    running = True
    clock = pygame.time.Clock()
    
    try:
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    elif event.key == pygame.K_1:
                        print("[TEST] Showing 1 finger (thumb only)")
                        simulator.show_fingers(1)
                    elif event.key == pygame.K_2:
                        print("[TEST] Showing 2 fingers (thumb + index)")
                        simulator.show_fingers(2)
                    elif event.key == pygame.K_3:
                        print("[TEST] Showing 3 fingers (thumb + index + middle)")
                        simulator.show_fingers(3)
                    elif event.key == pygame.K_4:
                        print("[TEST] Showing 4 fingers (thumb + index + middle + ring)")
                        simulator.show_fingers(4)
                    elif event.key == pygame.K_5:
                        print("[TEST] Showing 5 fingers (full hand)")
                        simulator.show_fingers(5)
                    elif event.key == pygame.K_w:
                        print("[TEST] Happy robot - WIN!")
                        simulator.show_reaction('win')
                    elif event.key == pygame.K_l:
                        print("[TEST] Sad robot - LOSE...")
                        simulator.show_reaction('lose')
            
            clock.tick(60)
    
    except KeyboardInterrupt:
        print("\n[TEST] Test interrupted")
    
    finally:
        print("[CLEANUP] Cleaning up...")
        simulator.stop()
        print("[TEST] Test complete!")

if __name__ == "__main__":
    main() 