import serial
import time
import threading
from queue import Queue, Empty

class ArduinoController:
    def __init__(self, port='COM3', baudrate=9600):
        """Set up connection to Arduino"""
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        self.connected = False
        self.button_callback = None
        self.message_queue = Queue()
        self.read_thread = None
        self.running = False
        
        # try to connect right away
        self.connect()
    
    def connect(self):
        """Try to connect to the Arduino"""
        try:
            print(f"[CONNECT] Attempting to connect to Arduino on {self.port}...")
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # give Arduino time to boot up
            self.connected = True
            self.running = True
            
            # start listening for Arduino messages
            self.read_thread = threading.Thread(target=self._read_serial)
            self.read_thread.daemon = True
            self.read_thread.start()
            
            print(f"[SUCCESS] Arduino connected on {self.port}")
            
            # let Arduino get ready
            time.sleep(1)
            
            # test if Arduino is responding
            print("[TEST] Testing Arduino communication...")
            self.send_command("RESET")
            time.sleep(0.5)
            
            return True
            
        except serial.SerialException as e:
            print(f"[ERROR] Failed to connect to Arduino on {self.port}: {e}")
            print("[INFO] Make sure:")
            print("   - Arduino is connected via USB")
            print("   - Correct COM port is specified")
            print("   - Arduino IDE Serial Monitor is closed")
            print("   - Try different ports: COM1, COM3, COM4, etc.")
            self.connected = False
            return False
        except Exception as e:
            print(f"[ERROR] Unexpected error connecting to Arduino: {e}")
            self.connected = False
            return False
    
    def _read_serial(self):
        """Listen for Arduino messages (runs in background thread)"""
        while self.running and self.connected:
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    message = self.serial_connection.readline().decode('utf-8').strip()
                    if message:
                        self.message_queue.put(message)
                        
                        # Arduino button was pressed
                        if message == "BUTTON_PRESSED" and self.button_callback:
                            self.button_callback()
                        
                        print(f"[ROBOT] Arduino: {message}")
                
                time.sleep(0.01)  # don't spam the CPU
                
            except Exception as e:
                print(f"[ERROR] Error reading from Arduino: {e}")
                break
    
    def send_command(self, command):
        """Send a command string to Arduino"""
        if not self.connected or not self.serial_connection:
            print(f"[ERROR] Cannot send command '{command}' - Arduino not connected")
            return False
        
        try:
            command_with_newline = command + '\n'
            self.serial_connection.write(command_with_newline.encode('utf-8'))
            self.serial_connection.flush()  # make sure it gets sent right away
            print(f"[SEND] Sent to Arduino: {command}")
            return True
        except Exception as e:
            print(f"[ERROR] Error sending command '{command}' to Arduino: {e}")
            return False
    
    def set_button_callback(self, callback_function):
        """Set callback function for button press events"""
        self.button_callback = callback_function
        print("[BUTTON] Button callback set")
    
    def countdown_3(self):
        """Trigger countdown 3 (red LED + beep)"""
        self.send_command("COUNTDOWN_3")
    
    def countdown_2(self):
        """Trigger countdown 2 (yellow LED + beep)"""
        self.send_command("COUNTDOWN_2")
    
    def countdown_1(self):
        """Trigger countdown 1 (green LED + beep)"""
        self.send_command("COUNTDOWN_1")
    
    def countdown_go(self):
        """Trigger GO signal (all LEDs flash + go sound)"""
        self.send_command("COUNTDOWN_GO")
    
    def player_wins(self):
        """Trigger player victory (celebration lights + victory sound)"""
        print("[SOUND] Sending PLAYER_WIN command to Arduino...")
        if self.send_command("PLAYER_WIN"):
            # Give Arduino more time to start the victory sequence (it's a long sequence)
            print("[SOUND] Victory command sent, waiting for Arduino to process...")
            time.sleep(0.5)  # Increased delay for longer victory sequence
            return True
        else:
            print("[ERROR] Failed to send PLAYER_WIN command")
            return False
    
    def player_loses(self):
        """Trigger player loss (sad sound + red LED)"""
        print("[SOUND] Sending PLAYER_LOSE command to Arduino...")
        if self.send_command("PLAYER_LOSE"):
            # Give Arduino more time to start the defeat sequence
            print("[SOUND] Defeat command sent, waiting for Arduino to process...")
            time.sleep(0.5)  # Increased delay for defeat sequence
            return True
        else:
            print("[ERROR] Failed to send PLAYER_LOSE command")
            return False
    
    def robot_wins(self):
        """Trigger robot victory (robot victory sound)"""
        print("[SOUND] Sending ROBOT_WIN command to Arduino...")
        if self.send_command("ROBOT_WIN"):
            # Give Arduino time to start the robot victory sequence
            print("[SOUND] Robot win command sent, waiting for Arduino to process...")
            time.sleep(0.3)
            return True
        else:
            print("[ERROR] Failed to send ROBOT_WIN command")
            return False
    
    def reset_leds(self):
        """Turn off all LEDs and stop sounds"""
        self.send_command("RESET")
    
    def show_game_start_message(self):
        """Show random game start message on LCD"""
        print("[LCD] Sending GAME_START command for random start message...")
        return self.send_command("GAME_START")
    
    def show_between_rounds_message(self):
        """Show random between-rounds message on LCD"""
        print("[LCD] Sending BETWEEN_ROUNDS command for random ready message...")
        return self.send_command("BETWEEN_ROUNDS")
    
    def show_player_round_win_message(self):
        """Show random player round win message on LCD"""
        print("[LCD] Sending PLAYER_ROUND_WIN command...")
        return self.send_command("PLAYER_ROUND_WIN")
    
    def show_robot_round_win_message(self):
        """Show random robot round win message on LCD"""
        print("[LCD] Sending ROBOT_ROUND_WIN command...")
        return self.send_command("ROBOT_ROUND_WIN")

    def test_arduino(self):
        """Test all Arduino components"""
        self.send_command("TEST")
    
    def get_messages(self):
        """Get all pending messages from Arduino"""
        messages = []
        try:
            while True:
                message = self.message_queue.get_nowait()
                messages.append(message)
        except Empty:
            pass
        return messages
    
    def disconnect(self):
        """Disconnect from Arduino"""
        self.running = False
        
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1)
        
        if self.serial_connection:
            try:
                self.reset_leds()  # Turn off LEDs before disconnecting
                time.sleep(0.1)
                self.serial_connection.close()
            except:
                pass
            self.serial_connection = None
        
        self.connected = False
        print("[DISCONNECT] Arduino disconnected")
    
    def is_connected(self):
        """Check if Arduino is connected"""
        return self.connected
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.disconnect()


def find_arduino_port():
    """
    Helper function to find Arduino port automatically
    Returns the first available serial port that might be an Arduino
    """
    import serial.tools.list_ports
    
    ports = serial.tools.list_ports.comports()
    arduino_ports = []
    
    for port in ports:
        # Look for common Arduino identifiers
        if any(keyword in port.description.lower() for keyword in ['arduino', 'ch340', 'cp210', 'ftdi']):
            arduino_ports.append(port.device)
        elif any(keyword in port.manufacturer.lower() if port.manufacturer else '' for keyword in ['arduino', 'microsoft']):
            arduino_ports.append(port.device)
    
    if arduino_ports:
        print(f"[FOUND] Found potential Arduino ports: {arduino_ports}")
        return arduino_ports[0]
    else:
        print("[SEARCH] No Arduino ports found automatically")
        print("Available ports:")
        for port in ports:
            print(f"  - {port.device}: {port.description}")
        return None


# Example usage and testing
if __name__ == "__main__":
    print("[TEST] Testing Arduino Controller")
    
    # Try to find Arduino automatically
    auto_port = find_arduino_port()
    if auto_port:
        arduino = ArduinoController(port=auto_port)
    else:
        # Fallback to common Windows port
        arduino = ArduinoController(port='COM3')
    
    if arduino.is_connected():
        print("[SUCCESS] Arduino controller test successful!")
        
        # Test sequence
        print("[TEST] Running test sequence...")
        time.sleep(1)
        
        arduino.countdown_3()
        time.sleep(1)
        arduino.countdown_2()
        time.sleep(1)
        arduino.countdown_1()
        time.sleep(1)
        arduino.countdown_go()
        time.sleep(2)
        
        arduino.player_wins()
        time.sleep(3)
        
        arduino.reset_leds()
        print("[TEST] Test complete!")
    else:
        print("[ERROR] Arduino controller test failed!")
    
    # Cleanup
    arduino.disconnect() 