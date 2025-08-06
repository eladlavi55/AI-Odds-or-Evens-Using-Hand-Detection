import json
import pickle
import os
from datetime import datetime
import numpy as np
from config import GAME_HISTORY_FILE, AI_MODEL_FILE, STATISTICS_FILE

try:
    from river import linear_model, preprocessing, compose, metrics
    RIVER_AVAILABLE = True
except ImportError:
    print("Warning: River library not installed. AI predictions disabled.")
    print("Install with: pip install river")
    RIVER_AVAILABLE = False

class AIPredictor:
    def __init__(self):
        """Set up the AI brain that learns player patterns"""
        self.river_available = RIVER_AVAILABLE
        
        if self.river_available:
            # model to guess how many fingers player will show
            self.finger_model = compose.Pipeline(
                preprocessing.StandardScaler(),
                linear_model.LinearRegression()
            )
            
            # model to guess if player will pick odds or evens
            self.choice_model = compose.Pipeline(
                preprocessing.StandardScaler(),
                linear_model.LogisticRegression()
            )
            
            # keep track of how well we're doing
            self.finger_metric = metrics.MAE()
            self.choice_metric = metrics.Accuracy()
        
        # store all the game data
        self.game_history = []
        self.player_stats = {
            'total_games': 0,
            'total_rounds': 0,
            'finger_counts': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            'choice_history': {'odds': 0, 'evens': 0},
            'win_rate': 0.0,
            'patterns': {}
        }
        
        # our latest guesses
        self.last_predictions = {
            'finger_count': 3,
            'choice': 'odds',
            'confidence': 0.0
        }
        
        # load any saved data from previous sessions
        self.load_data()
    
    def extract_features(self, game_state):
        """Turn the game state into numbers the AI can understand"""
        features = {}
        
        # what time is it? (people might play differently at different times)
        now = datetime.now()
        features['hour'] = now.hour
        features['minute'] = now.minute
        features['day_of_week'] = now.weekday()
        
        # what's happening in the current game?
        features['current_round'] = game_state.get('current_round', 1)
        features['player_wins'] = game_state.get('player_wins', 0)
        features['robot_wins'] = game_state.get('robot_wins', 0)
        features['rounds_played'] = len(self.game_history)
        
        # look at what they did recently
        if len(self.game_history) > 0:
            recent_games = self.game_history[-5:]  # just look at the last few rounds
            
            # what fingers they've been showing
            recent_fingers = [g.get('player_fingers', 3) for g in recent_games]
            features['avg_recent_fingers'] = np.mean(recent_fingers) if recent_fingers else 3
            features['last_finger_count'] = recent_fingers[-1] if recent_fingers else 3
            
            # do they prefer odds or evens lately?
            recent_choices = [1 if g.get('player_choice') == 'odds' else 0 for g in recent_games]
            features['recent_odds_ratio'] = np.mean(recent_choices) if recent_choices else 0.5
            
            # are they winning or losing?
            recent_wins = [1 if g.get('player_won_round', False) else 0 for g in recent_games]
            features['recent_win_rate'] = np.mean(recent_wins) if recent_wins else 0.5
        else:
            features['avg_recent_fingers'] = 3
            features['last_finger_count'] = 3
            features['recent_odds_ratio'] = 0.5
            features['recent_win_rate'] = 0.5
        
        # do they change their finger count between rounds?
        if len(self.game_history) >= 2:
            last_two_fingers = [self.game_history[-1].get('player_fingers', 3),
                              self.game_history[-2].get('player_fingers', 3)]
            features['finger_change'] = last_two_fingers[0] - last_two_fingers[1]
        else:
            features['finger_change'] = 0
        
        return features
    
    def predict_player_behavior(self, game_state):
        """Try to guess what the player will do next"""
        if not self.river_available:
            # just use basic stats if no fancy AI
            return self._simple_prediction()
        
        features = self.extract_features(game_state)
        
        try:
            # guess how many fingers
            finger_features = {k: v for k, v in features.items()}
            predicted_fingers = self.finger_model.predict_one(finger_features)
            predicted_fingers = max(1, min(5, round(predicted_fingers)))
            
            # guess odds or evens
            choice_features = {k: v for k, v in features.items()}
            choice_proba = self.choice_model.predict_proba_one(choice_features)
            
            if choice_proba:
                odds_prob = choice_proba.get(True, 0.5)  # True means odds
                predicted_choice = 'odds' if odds_prob > 0.5 else 'evens'
                confidence = abs(odds_prob - 0.5) * 2  # how sure are we?
            else:
                predicted_choice = 'odds'
                confidence = 0.0
            
            self.last_predictions = {
                'finger_count': predicted_fingers,
                'choice': predicted_choice,
                'confidence': confidence
            }
            
            # show what we think will happen
            self._print_prediction_info(features, predicted_fingers, predicted_choice, confidence)
            
        except Exception as e:
            print(f"Prediction error: {e}")
            self.last_predictions = self._simple_prediction()
        
        return self.last_predictions
    
    def _simple_prediction(self):
        """Basic prediction using what they did most often"""
        # what finger count do they use most?
        finger_counts = self.player_stats['finger_counts']
        if sum(finger_counts.values()) > 0:
            most_common_fingers = max(finger_counts, key=finger_counts.get)
        else:
            most_common_fingers = 3
        
        # do they prefer odds or evens?
        choice_history = self.player_stats['choice_history']
        if sum(choice_history.values()) > 0:
            most_common_choice = max(choice_history, key=choice_history.get)
        else:
            most_common_choice = 'odds'
        
        return {
            'finger_count': most_common_fingers,
            'choice': most_common_choice,
            'confidence': 0.1  # not very confident without fancy AI
        }
    
    def _print_prediction_info(self, features, predicted_fingers, predicted_choice, confidence):
        """Show what the AI is thinking to the terminal"""
        print("\n" + "="*50)
        print(f"[PREDICTION] Round {features.get('current_round', 1)}")
        print("="*50)
        
        # what patterns do we see?
        print(f"Most used fingers: {features.get('most_common_finger', 3)}")
        print(f"Recent choice preference: {predicted_choice.upper()}")
        print(f"Win rate so far: {features.get('win_rate', 0.0):.1%}")
        
        # what happened lately?
        if features.get('recent_finger_avg', 0) > 0:
            print(f"Recent finger average: {features.get('recent_finger_avg', 0):.1f}")
        
        # our guess for this round
        print(f"\n[ROBOT STRATEGY]")
        print(f"Predicted finger count: {predicted_fingers}")
        print(f"Predicted choice: {predicted_choice.upper()}")
        print(f"Confidence: {confidence:.1%}")
        
        print("="*50 + "\n")
    
    def update_model(self, game_data):
        """Learn from what just happened in the game"""
        if not self.river_available:
            # just keep basic stats if no fancy AI
            self._update_statistics(game_data)
            return
        
        # turn the game result into numbers for the AI
        features = self.extract_features({'current_round': game_data.get('current_round', 1)})
        
        # what actually happened?
        actual_fingers = game_data.get('player_fingers', 3)
        actual_choice = game_data.get('player_choice', 'odds')
        actual_choice_binary = actual_choice == 'odds'
        
        try:
            # teach the finger-counting AI
            self.finger_model.learn_one(features, actual_fingers)
            
            # teach the odds/evens AI
            self.choice_model.learn_one(features, actual_choice_binary)
            
            # see how well we did
            if 'finger_count' in self.last_predictions:
                predicted_fingers = self.last_predictions['finger_count']
                self.finger_metric.update(actual_fingers, predicted_fingers)
            
            if 'choice' in self.last_predictions:
                predicted_choice = self.last_predictions['choice'] == 'odds'
                self.choice_metric.update(actual_choice_binary, predicted_choice)
            
        except Exception as e:
            print(f"Model update error: {e}")
        
        # save this round to our records
        self._update_statistics(game_data)
        self.game_history.append(game_data)
        
        # the game engine handles saving everything to files
    
    def _update_statistics(self, game_data):
        """update player statistics"""
        self.player_stats['total_rounds'] += 1
        
        # update finger count statistics
        fingers = game_data.get('player_fingers', 3)
        if 1 <= fingers <= 5:
            # use str(fingers) as key to match JSON format
            # this prevents KeyErrors if the file has string keys
            finger_key = str(fingers)
            if finger_key not in self.player_stats['finger_counts']:
                self.player_stats['finger_counts'][finger_key] = 0
            self.player_stats['finger_counts'][finger_key] += 1
        
        # update choice statistics
        choice = game_data.get('player_choice', 'odds')
        if choice in ['odds', 'evens']:
            self.player_stats['choice_history'][choice] += 1
        
        # update game count and win rate
        if game_data.get('game_finished', False):
            self.player_stats['total_games'] += 1
        
        # calculate win rate based on all rounds played
        if self.player_stats['total_rounds'] > 0:
            # ensure game_history is populated before calculating win rate
            history_wins = sum(1 for g in self.game_history if g.get('player_won_round', False))
            current_win = 1 if game_data.get('player_won_round', False) else 0
            total_wins = history_wins + current_win
            
            # use total_rounds which includes the current round
            self.player_stats['win_rate'] = total_wins / self.player_stats['total_rounds']
        
        print(f"[STATS] Updated stats - Rounds: {self.player_stats['total_rounds']}, Games: {self.player_stats['total_games']}, Win rate: {self.player_stats['win_rate']:.2%}")
    
    def get_robot_strategy(self, predicted_player_fingers, predicted_choice):
        """Figure out what number the robot should show to try to win"""
        try:
            # basic strategy: if player picked odds, try to make total even (so robot wins)
            
            # opposite of what player wants = robot wins
            
            target_parity = 'even' if predicted_choice == 'odds' else 'odd'
            
            # which robot numbers (1-5) would give us what we want?
            good_choices = []
            for robot_fingers in range(1, 6):
                total = predicted_player_fingers + robot_fingers
                total_parity = 'odd' if total % 2 == 1 else 'even'
                if total_parity == target_parity:
                    good_choices.append(robot_fingers)
            
            if good_choices:
                # pick randomly so we're not too predictable
                import random
                return random.choice(good_choices)
            else:
                # if nothing good, just go random
                return random.randint(1, 5)
                
        except Exception as e:
            print(f"[ERROR] Error in robot strategy: {e}")
            return 3  # safe default
    
    def save_data(self):
        """save game history and model to files"""
        try:
            # ensure directories exist
            os.makedirs(os.path.dirname(GAME_HISTORY_FILE), exist_ok=True)
            
            # save game history
            with open(GAME_HISTORY_FILE, 'w') as f:
                json.dump(self.game_history, f, indent=2, default=str)
            print(f"[SAVE] Saved {len(self.game_history)} game records to {GAME_HISTORY_FILE}")
            
            # save statistics
            with open(STATISTICS_FILE, 'w') as f:
                json.dump(self.player_stats, f, indent=2)
            print(f"[STATS] Saved statistics to {STATISTICS_FILE}")
            
            # save AI model (if River is available)
            if self.river_available:
                try:
                    model_data = {
                        'finger_model': self.finger_model,
                        'choice_model': self.choice_model,
                        'finger_metric': self.finger_metric,
                        'choice_metric': self.choice_metric
                    }
                    with open(AI_MODEL_FILE, 'wb') as f:
                        pickle.dump(model_data, f)
                    print(f"[AI] Saved AI model to {AI_MODEL_FILE}")
                except Exception as model_error:
                    print(f"Warning: Could not save AI model: {model_error}")
            
            print("[SUCCESS] All data saved successfully")
            
        except Exception as e:
            print(f"[ERROR] Error saving data: {e}")
            import traceback
            traceback.print_exc()
    
    def load_data(self):
        """load game history and model from files"""
        try:
            # load game history
            if os.path.exists(GAME_HISTORY_FILE):
                with open(GAME_HISTORY_FILE, 'r') as f:
                    # added a check to handle empty or invalid JSON file
                    try:
                        loaded_history = json.load(f)
                        if isinstance(loaded_history, list):
                            self.game_history = loaded_history
                            print(f"Loaded {len(self.game_history)} historical rounds")
                        else:
                            print("Invalid game history format, starting fresh")
                            self.game_history = []
                    except json.JSONDecodeError:
                        print("Could not decode game history, starting fresh.")
                        self.game_history = []
            
            # load statistics
            if os.path.exists(STATISTICS_FILE):
                with open(STATISTICS_FILE, 'r') as f:
                    try:
                        loaded_stats = json.load(f)
                        if isinstance(loaded_stats, dict):
                            # ensure all required keys exist
                            required_keys = ['total_games', 'total_rounds', 'finger_counts', 'choice_history', 'win_rate']
                            if all(key in loaded_stats for key in required_keys):
                                self.player_stats = loaded_stats
                                print(f"Loaded player statistics: {self.player_stats['total_games']} games played")
                                
                                # ensure finger_counts has all keys from 1-5
                                for i in range(1, 6):
                                    # use .get() to avoid KeyError if a key is missing in the file
                                    if str(i) not in self.player_stats['finger_counts']:
                                         self.player_stats['finger_counts'][str(i)] = 0
                            else:
                                print("Incomplete statistics format, using default")
                    except json.JSONDecodeError:
                        print("Could not decode statistics file, using default.")
            
            # load AI model (if River is available and file exists)
            if self.river_available and os.path.exists(AI_MODEL_FILE):
                try:
                    with open(AI_MODEL_FILE, 'rb') as f:
                        model_data = pickle.load(f)
                        self.finger_model = model_data.get('finger_model', self.finger_model)
                        self.choice_model = model_data.get('choice_model', self.choice_model)
                        self.finger_metric = model_data.get('finger_metric', self.finger_metric)
                        self.choice_metric = model_data.get('choice_metric', self.choice_metric)
                    print("AI model loaded successfully")
                except Exception as model_error:
                    print(f"Error loading AI model: {model_error}")
                    print("Starting with fresh AI model")
                
        except Exception as e:
            print(f"Error loading data: {e}")
            print("Starting with fresh data")
    
    def reset_data(self):
        """reset all data and models"""
        self.game_history = []
        self.player_stats = {
            'total_games': 0,
            'total_rounds': 0,
            'finger_counts': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            'choice_history': {'odds': 0, 'evens': 0},
            'win_rate': 0.0,
            'patterns': {}
        }
        
        if self.river_available:
            # reset models
            self.finger_model = compose.Pipeline(
                preprocessing.StandardScaler(),
                linear_model.LinearRegression()
            )
            self.choice_model = compose.Pipeline(
                preprocessing.StandardScaler(),
                linear_model.LogisticRegression()
            )
            self.finger_metric = metrics.MAE()
            self.choice_metric = metrics.Accuracy()
        
        print("AI data and models reset") 