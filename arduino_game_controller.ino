/*
  Arduino code for the finger counting game
  
  Wiring:
  - Red LED on pin 13 (220Ω resistor)
  - Yellow LED on pin 12 (220Ω resistor) 
  - Green LED on pin 11 (220Ω resistor)
  - Buzzer on pin 9 (just connect + to pin 9, - to ground)
  - Button on pin 2 (other side to ground, needs 10k pullup)
  - LCD: pin 8=RS, 7=enable, 6-3=data pins D4-D7
  
  What Python can send:
  COUNTDOWN_3/2/1 - light up LEDs and beep for countdown
  COUNTDOWN_GO - flash all LEDs, play go sound
  PLAYER_WIN/LOSE - victory/defeat sounds and lights
  ROBOT_WIN - robot victory sound
  GAME_START/PLAYER_ROUND_WIN/ROBOT_ROUND_WIN/BETWEEN_ROUNDS - random LCD messages
  RESET - turn everything off, show ready message
  TEST - test all the hardware
*/

#include <LiquidCrystal.h>
#include <avr/pgmspace.h>

// pin connections
const int RED_LED = 13;
const int YELLOW_LED = 12;
const int GREEN_LED = 11;
const int BUZZER = 9;
const int BUTTON = 2;

// LCD connected to these pins
LiquidCrystal lcd(8, 7, 6, 5, 4, 3);

// button debouncing stuff
bool lastButtonState = HIGH;
bool currentButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;

// different tones for different events
const int FREQ_COUNTDOWN = 800;   // Countdown beep
const int FREQ_GO = 1200;         // Go sound
const int FREQ_WIN_HIGH = 1500;   // Victory high note
const int FREQ_WIN_LOW = 1000;    // Victory low note
const int FREQ_LOSE = 300;        // Sad/lose sound
const int FREQ_ROBOT_WIN = 600;   // Robot win sound

// all the LCD messages - stored in flash memory to save RAM
// messages for when game starts
const char gameStart0[] PROGMEM = "Ready to get";
const char gameStart1[] PROGMEM = "schooled?";
const char gameStart2[] PROGMEM = "Let's see what";
const char gameStart3[] PROGMEM = "you got, human!";
const char gameStart4[] PROGMEM = "Finger fight!";
const char gameStart5[] PROGMEM = "May odds be ever";
const char gameStart6[] PROGMEM = "Beep boop!";
const char gameStart7[] PROGMEM = "Game time!";
const char gameStart8[] PROGMEM = "Human vs Robot";
const char gameStart9[] PROGMEM = "Let's rumble!";

const char* const gameStartMessages[] PROGMEM = {
  gameStart0, gameStart1, gameStart2, gameStart3, gameStart4,
  gameStart5, gameStart6, gameStart7, gameStart8, gameStart9
};

// Player Loses Game Messages (5 reduced)
const char playerLose0[] PROGMEM = "Better luck";
const char playerLose1[] PROGMEM = "next time!";
const char playerLose2[] PROGMEM = "My circuits are";
const char playerLose3[] PROGMEM = "superior!";
const char playerLose4[] PROGMEM = "Humans: 0";
const char playerLose5[] PROGMEM = "Robots: 1";
const char playerLose6[] PROGMEM = "Victory.exe";
const char playerLose7[] PROGMEM = "completed!";
const char playerLose8[] PROGMEM = "Resistance is";
const char playerLose9[] PROGMEM = "futile!";

const char* const playerLoseMessages[] PROGMEM = {
  playerLose0, playerLose1, playerLose2, playerLose3, playerLose4,
  playerLose5, playerLose6, playerLose7, playerLose8, playerLose9
};

// Player Wins Game Messages (5 reduced)
const char playerWin0[] PROGMEM = "Impressive,";
const char playerWin1[] PROGMEM = "human!";
const char playerWin2[] PROGMEM = "You got lucky";
const char playerWin3[] PROGMEM = "this time!";
const char playerWin4[] PROGMEM = "Well played,";
const char playerWin5[] PROGMEM = "meatbag!";
const char playerWin6[] PROGMEM = "Your victory";
const char playerWin7[] PROGMEM = "is temporary!";
const char playerWin8[] PROGMEM = "System crash:";
const char playerWin9[] PROGMEM = "Ego.exe stopped";

const char* const playerWinMessages[] PROGMEM = {
  playerWin0, playerWin1, playerWin2, playerWin3, playerWin4,
  playerWin5, playerWin6, playerWin7, playerWin8, playerWin9
};

// Player Round Win Messages (5 reduced)
const char playerRound0[] PROGMEM = "You win";
const char playerRound1[] PROGMEM = "this round!";
const char playerRound2[] PROGMEM = "Human takes";
const char playerRound3[] PROGMEM = "the point!";
const char playerRound4[] PROGMEM = "Nice fingers!";
const char playerRound5[] PROGMEM = "You win!";
const char playerRound6[] PROGMEM = "Victory dance";
const char playerRound7[] PROGMEM = "permitted!";
const char playerRound8[] PROGMEM = "Success.exe";
const char playerRound9[] PROGMEM = "for human!";

const char* const playerRoundWinMessages[] PROGMEM = {
  playerRound0, playerRound1, playerRound2, playerRound3, playerRound4,
  playerRound5, playerRound6, playerRound7, playerRound8, playerRound9
};

// Robot Round Win Messages (5 reduced)
const char robotRound0[] PROGMEM = "Robot takes";
const char robotRound1[] PROGMEM = "the point!";
const char robotRound2[] PROGMEM = "My circuits";
const char robotRound3[] PROGMEM = "are pleased!";
const char robotRound4[] PROGMEM = "Beep boop!";
const char robotRound5[] PROGMEM = "I win!";
const char robotRound6[] PROGMEM = "Superior logic";
const char robotRound7[] PROGMEM = "prevails!";
const char robotRound8[] PROGMEM = "Human error";
const char robotRound9[] PROGMEM = "detected!";

const char* const robotRoundWinMessages[] PROGMEM = {
  robotRound0, robotRound1, robotRound2, robotRound3, robotRound4,
  robotRound5, robotRound6, robotRound7, robotRound8, robotRound9
};

// Between Rounds Messages (5 messages, 2 lines each)
const char betweenRounds0[] PROGMEM = "Ready for the";
const char betweenRounds1[] PROGMEM = "next battle?";
const char betweenRounds2[] PROGMEM = "Calculating...";
const char betweenRounds3[] PROGMEM = "Bring it on!";
const char betweenRounds4[] PROGMEM = "Systems ready!";
const char betweenRounds5[] PROGMEM = "Let's continue!";
const char betweenRounds6[] PROGMEM = "Round incoming";
const char betweenRounds7[] PROGMEM = "in 3... 2... 1!";
const char betweenRounds8[] PROGMEM = "My circuits are";
const char betweenRounds9[] PROGMEM = "warmed up!";

const char* const betweenRoundsMessages[] PROGMEM = {
  betweenRounds0, betweenRounds1, betweenRounds2, betweenRounds3, betweenRounds4,
  betweenRounds5, betweenRounds6, betweenRounds7, betweenRounds8, betweenRounds9
};

// Buffer to read strings from PROGMEM
char buffer[17]; // 16 chars + null terminator

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Initialize random seed for message selection
  randomSeed(analogRead(0));
  
  // Initialize LCD
  lcd.begin(16, 2);
  lcd.clear();
  lcd.print("Game Controller");
  lcd.setCursor(0, 1);
  lcd.print("Initializing...");
  
  // Set pin modes
  pinMode(RED_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  pinMode(BUTTON, INPUT_PULLUP);
  
  // Turn off all LEDs initially
  digitalWrite(RED_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(GREEN_LED, LOW);
  
  // Startup sequence - quick test
  startupSequence();
  
  // Show random game start message on LCD
  showGameStartMessage();
  
  Serial.println("Arduino Game Controller Ready!");
  Serial.println("Commands: COUNTDOWN_3, COUNTDOWN_2, COUNTDOWN_1, COUNTDOWN_GO, PLAYER_WIN, PLAYER_LOSE, ROBOT_WIN, GAME_START, PLAYER_ROUND_WIN, ROBOT_ROUND_WIN, BETWEEN_ROUNDS, RESET, TEST");
}

void loop() {
  // Check for button press
  checkButton();
  
  // Check for serial commands from Python
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    processCommand(command);
  }
  
  delay(10); // Small delay to prevent overwhelming the serial
}

void checkButton() {
  // Read button with debouncing
  int reading = digitalRead(BUTTON);
  
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }
  
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != currentButtonState) {
      currentButtonState = reading;
      
      // Button pressed (LOW because of pull-up resistor)
      if (currentButtonState == LOW) {
        Serial.println("BUTTON_PRESSED");
        // Quick feedback beep
        tone(BUZZER, FREQ_COUNTDOWN, 100);
      }
    }
  }
  
  lastButtonState = reading;
}

void processCommand(String command) {
  Serial.println("Received: " + command);
  
  if (command == "COUNTDOWN_3") {
    countdown3();
  }
  else if (command == "COUNTDOWN_2") {
    countdown2();
  }
  else if (command == "COUNTDOWN_1") {
    countdown1();
  }
  else if (command == "COUNTDOWN_GO") {
    countdownGo();
  }
  else if (command == "PLAYER_WIN") {
    playerWin();
  }
  else if (command == "PLAYER_LOSE") {
    playerLose();
  }
  else if (command == "ROBOT_WIN") {
    robotWin();
  }
  else if (command == "GAME_START") {
    showGameStartMessage();
  }
  else if (command == "PLAYER_ROUND_WIN") {
    showPlayerRoundWinMessage();
  }
  else if (command == "ROBOT_ROUND_WIN") {
    showRobotRoundWinMessage();
  }
  else if (command == "BETWEEN_ROUNDS") {
    showBetweenRoundsMessage();
  }
  else if (command == "RESET") {
    resetLEDs();
  }
  else if (command == "TEST") {
    testSequence();
  }
  else {
    Serial.println("Unknown command: " + command);
  }
}

// LCD Message Display Functions (PROGMEM compatible)
void showGameStartMessage() {
  int messageIndex = random(0, 5) * 2; // Each message has 2 lines (5 messages total)
  lcd.clear();
  strcpy_P(buffer, (char*)pgm_read_word(&(gameStartMessages[messageIndex])));
  lcd.print(buffer);
  lcd.setCursor(0, 1);
  strcpy_P(buffer, (char*)pgm_read_word(&(gameStartMessages[messageIndex + 1])));
  lcd.print(buffer);
  Serial.println("Game start message displayed");
}

void showPlayerLoseMessage() {
  int messageIndex = random(0, 5) * 2;
  lcd.clear();
  strcpy_P(buffer, (char*)pgm_read_word(&(playerLoseMessages[messageIndex])));
  lcd.print(buffer);
  lcd.setCursor(0, 1);
  strcpy_P(buffer, (char*)pgm_read_word(&(playerLoseMessages[messageIndex + 1])));
  lcd.print(buffer);
  Serial.println("Player lose message displayed");
}

void showPlayerWinMessage() {
  int messageIndex = random(0, 5) * 2;
  lcd.clear();
  strcpy_P(buffer, (char*)pgm_read_word(&(playerWinMessages[messageIndex])));
  lcd.print(buffer);
  lcd.setCursor(0, 1);
  strcpy_P(buffer, (char*)pgm_read_word(&(playerWinMessages[messageIndex + 1])));
  lcd.print(buffer);
  Serial.println("Player win message displayed");
}

void showPlayerRoundWinMessage() {
  int messageIndex = random(0, 5) * 2;
  lcd.clear();
  strcpy_P(buffer, (char*)pgm_read_word(&(playerRoundWinMessages[messageIndex])));
  lcd.print(buffer);
  lcd.setCursor(0, 1);
  strcpy_P(buffer, (char*)pgm_read_word(&(playerRoundWinMessages[messageIndex + 1])));
  lcd.print(buffer);
  Serial.println("Player round win message displayed");
}

void showRobotRoundWinMessage() {
  int messageIndex = random(0, 5) * 2;
  lcd.clear();
  strcpy_P(buffer, (char*)pgm_read_word(&(robotRoundWinMessages[messageIndex])));
  lcd.print(buffer);
  lcd.setCursor(0, 1);
  strcpy_P(buffer, (char*)pgm_read_word(&(robotRoundWinMessages[messageIndex + 1])));
  lcd.print(buffer);
  Serial.println("Robot round win message displayed");
}

void showBetweenRoundsMessage() {
  int messageIndex = random(0, 5) * 2;
  lcd.clear();
  strcpy_P(buffer, (char*)pgm_read_word(&(betweenRoundsMessages[messageIndex])));
  lcd.print(buffer);
  lcd.setCursor(0, 1);
  strcpy_P(buffer, (char*)pgm_read_word(&(betweenRoundsMessages[messageIndex + 1])));
  lcd.print(buffer);
  Serial.println("Between rounds message displayed");
}

void countdown3() {
  resetLEDs();
  digitalWrite(RED_LED, HIGH);
  tone(BUZZER, FREQ_COUNTDOWN, 500);
  Serial.println("Countdown: 3");
}

void countdown2() {
  resetLEDs();
  digitalWrite(YELLOW_LED, HIGH);
  tone(BUZZER, FREQ_COUNTDOWN, 500);
  Serial.println("Countdown: 2");
}

void countdown1() {
  resetLEDs();
  digitalWrite(GREEN_LED, HIGH);
  tone(BUZZER, FREQ_COUNTDOWN, 500);
  Serial.println("Countdown: 1");
}

void countdownGo() {
  // Flash all LEDs
  for (int i = 0; i < 3; i++) {
    digitalWrite(RED_LED, HIGH);
    digitalWrite(YELLOW_LED, HIGH);
    digitalWrite(GREEN_LED, HIGH);
    tone(BUZZER, FREQ_GO, 200);
    delay(200);
    resetLEDs();
    delay(100);
  }
  Serial.println("GO!");
}

void playerWin() {
  Serial.println("Player Wins!");
  
  // Show random player win message on LCD
  showPlayerWinMessage();
  
  // Victory light show and sound
  for (int i = 0; i < 5; i++) {
    // High note with green LED
    digitalWrite(GREEN_LED, HIGH);
    tone(BUZZER, FREQ_WIN_HIGH, 300);
    delay(300);
    digitalWrite(GREEN_LED, LOW);
    
    // Low note with yellow LED
    digitalWrite(YELLOW_LED, HIGH);
    tone(BUZZER, FREQ_WIN_LOW, 300);
    delay(300);
    digitalWrite(YELLOW_LED, LOW);
  }
  
  // Final celebration - all LEDs flash
  for (int i = 0; i < 10; i++) {
    digitalWrite(RED_LED, HIGH);
    digitalWrite(YELLOW_LED, HIGH);
    digitalWrite(GREEN_LED, HIGH);
    delay(100);
    digitalWrite(RED_LED, LOW);
    digitalWrite(YELLOW_LED, LOW);
    digitalWrite(GREEN_LED, LOW);
    delay(100);
  }
}

void playerLose() {
  Serial.println("Player Loses!");
  
  // Show random player lose message on LCD
  showPlayerLoseMessage();
  
  // Sad sound with red LED
  digitalWrite(RED_LED, HIGH);
  for (int i = 0; i < 3; i++) {
    tone(BUZZER, FREQ_LOSE, 800);
    delay(800);
    noTone(BUZZER);
    delay(200);
  }
  
  // Slow red LED fade effect
  for (int i = 0; i < 3; i++) {
    digitalWrite(RED_LED, LOW);
    delay(300);
    digitalWrite(RED_LED, HIGH);
    delay(300);
  }
  
  resetLEDs();
}

void robotWin() {
  Serial.println("Robot Wins!");
  
  // Robot victory sound - mechanical beeping
  for (int i = 0; i < 8; i++) {
    digitalWrite(RED_LED, HIGH);
    tone(BUZZER, FREQ_ROBOT_WIN, 150);
    delay(150);
    digitalWrite(RED_LED, LOW);
    noTone(BUZZER);
    delay(100);
  }
}

void resetLEDs() {
  digitalWrite(RED_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(GREEN_LED, LOW);
  noTone(BUZZER);
  
  // Note: LCD message should be set by specific command (GAME_START, BETWEEN_ROUNDS, etc.)
  // This function only resets hardware, not LCD display
}

void startupSequence() {
  // Quick startup test
  digitalWrite(RED_LED, HIGH);
  tone(BUZZER, 1000, 200);
  delay(200);
  
  digitalWrite(YELLOW_LED, HIGH);
  tone(BUZZER, 1200, 200);
  delay(200);
  
  digitalWrite(GREEN_LED, HIGH);
  tone(BUZZER, 1400, 200);
  delay(200);
  
  resetLEDs();
  delay(500);
}

void testSequence() {
  Serial.println("Testing all components...");
  
  // Test LCD
  Serial.println("Testing LCD...");
  lcd.clear();
  lcd.print("LCD Test 1/2");
  lcd.setCursor(0, 1);
  lcd.print("Display working!");
  delay(2000);
  
  lcd.clear();
  lcd.print("LCD Test 2/2");
  lcd.setCursor(0, 1);
  lcd.print("All good!");
  delay(2000);
  
  // Test LEDs
  Serial.println("Testing LEDs...");
  lcd.clear();
  lcd.print("Testing LEDs...");
  digitalWrite(RED_LED, HIGH);
  delay(500);
  digitalWrite(YELLOW_LED, HIGH);
  delay(500);
  digitalWrite(GREEN_LED, HIGH);
  delay(500);
  digitalWrite(RED_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(GREEN_LED, LOW);
  
  // Test buzzer
  Serial.println("Testing buzzer...");
  lcd.clear();
  lcd.print("Testing buzzer...");
  tone(BUZZER, 500, 500);
  delay(600);
  tone(BUZZER, 1000, 500);
  delay(600);
  tone(BUZZER, 1500, 500);
  delay(600);
  
  // Test button (wait for press)
  Serial.println("Press the button to complete test...");
  lcd.clear();
  lcd.print("Press button to");
  lcd.setCursor(0, 1);
  lcd.print("complete test!");
  
  while (digitalRead(BUTTON) == HIGH) {
    delay(10);
  }
  
  // Button pressed
  tone(BUZZER, 2000, 200);
  digitalWrite(GREEN_LED, HIGH);
  lcd.clear();
  lcd.print("Test Complete!");
  lcd.setCursor(0, 1);
  lcd.print("All systems OK!");
  delay(2000);
  resetLEDs();
  
  Serial.println("Test complete!");
} 