import json
import os
import time

class ContestManager:
    def __init__(self, state_file='contest_state.json', data_file='contest_data.json'):
        self.state_file = state_file
        self.data_file = data_file
        self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                self.start_time = data.get('start_time', time.time())
                self.end_time = data.get('end_time', time.time() + 3600)
        else:
            self.start_time = time.time()
            self.end_time = self.start_time + 5 * 3600 # 5 hours default
            self._save_state()

    def _save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump({'start_time': self.start_time, 'end_time': self.end_time}, f)

    def get_time_remaining(self):
        return max(0, self.end_time - time.time())

    def is_over(self):
        return time.time() > self.end_time

    def get_user_submissions(self, username):
        data = self._load_data()
        return data.get(username, [])

    def save_submission(self, username, problem_id, verdict, score):
        data = self._load_data()
        if username not in data:
            data[username] = []
        
        submission = {
            'time': time.strftime('%H:%M:%S'),
            'timestamp': time.time(),
            'problem': problem_id,
            'verdict': verdict,
            'score': score
        }
        data[username].insert(0, submission) # Add to beginning
        self._save_data(data)

    def _load_data(self):
        if not os.path.exists(self.data_file):
            return {}
        with open(self.data_file, 'r') as f:
            return json.load(f)

    def _save_data(self, data):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    def get_leaderboard(self, all_users):
        data = self._load_data()
        leaderboard = []
        
        for user in all_users:
            subs = data.get(user, [])
            best_scores = {} # problem_id -> max_score
            
            for sub in subs:
                pid = sub['problem']
                # Ensure score is treated as int/float
                try:
                    score = float(sub.get('score', 0))
                except:
                    score = 0
                    
                if pid not in best_scores:
                    best_scores[pid] = score
                else:
                    best_scores[pid] = max(best_scores[pid], score)
            
            total_score = sum(best_scores.values())
            
            leaderboard.append({
                'username': user,
                'total_score': int(total_score), # Display as int usually
                'breakdown': best_scores
            })
            
        # Sort by total score descending
        leaderboard.sort(key=lambda x: x['total_score'], reverse=True)
        return leaderboard

    def update_ratings(self, user_manager):
        # Simple ELO-like implementation
        # Get leaderboard
        users = list(user_manager.users.keys())
        leaderboard = self.get_leaderboard(users)
        
        # Map username -> rank (0-indexed)
        ranks = {entry['username']: i for i, entry in enumerate(leaderboard)}
        
        # Calculate new ratings
        new_ratings = {}
        K = 32 # K-factor
        
        for user_a in users:
            ra = user_manager.get_rating(user_a)
            expected_sum = 0
            actual_sum = 0
            
            for user_b in users:
                if user_a == user_b: continue
                
                rb = user_manager.get_rating(user_b)
                
                # Expected score A vs B
                ea = 1 / (1 + 10 ** ((rb - ra) / 400))
                expected_sum += ea
                
                # Actual score A vs B
                # If A ranked higher (lower index) than B => win (1.0)
                # If A ranked lower than B => loss (0.0)
                # Tie? (same total score) => 0.5 (Need to handle ties in ranks)
                
                rank_a = ranks[user_a]
                rank_b = ranks[user_b]
                
                # Handle ties: check total scores
                score_a = leaderboard[rank_a]['total_score']
                score_b = leaderboard[rank_b]['total_score']
                
                if score_a > score_b:
                    sa = 1.0
                elif score_a < score_b:
                    sa = 0.0
                else:
                    sa = 0.5
                
                actual_sum += sa
            
            # Update
            # In multi-player, often we treat it as (Actual - Expected) * K / (N-1) or similar.
            # Or just sum of pairwise updates.
            # Codeforces is more complex (seed, geometric mean), but this is "Codeforces-esque" enough for a prototype.
            
            if len(users) > 1:
                change = K * (actual_sum - expected_sum)
                # Normalize change by number of opponents to avoid huge swings?
                # Standard Elo pairwise sum is fine if K is small per game, but here we sum over all.
                # Let's use K / (N-1) effectively or just a smaller K.
                # With K=32 and summing all pairs, changes will be huge.
                # Let's use K = 32 / (len(users) - 1) * 2 or something.
                # Simplified: NewRating = Old + K * (Actual - Expected) is for 1v1.
                # Here we sum (Actual - Expected).
                # Let's divide by number of opponents.
                change = (K * (actual_sum - expected_sum)) / (len(users) - 1)
            else:
                change = 0

            new_ratings[user_a] = ra + int(change)

        # Apply updates
        for user, rating in new_ratings.items():
            user_manager.users[user]['rating'] = rating
        
        # Save users
        with open(user_manager.users_file, 'w') as f:
            json.dump(user_manager.users, f, indent=4)

