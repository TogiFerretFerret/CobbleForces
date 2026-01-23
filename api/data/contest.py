import json
import os
import time

class ContestManager:
    def __init__(self, contests_file='api/data/contests.json', data_file='contest_data.json'):
        self.contests_file = contests_file
        self.data_file = data_file
        self.contests = self._load_contests()

    def _load_contests(self):
        if os.path.exists(self.contests_file):
            with open(self.contests_file, 'r') as f:
                return json.load(f)
        return {}

    def save_contests(self):
        with open(self.contests_file, 'w') as f:
            json.dump(self.contests, f, indent=4)

    def create_contest(self, name, start_time, end_time):
        # Generate new ID
        ids = [int(k) for k in self.contests.keys()]
        new_id = str(max(ids) + 1) if ids else "1"
        
        self.contests[new_id] = {
            "id": new_id,
            "name": name,
            "start_time": float(start_time),
            "end_time": float(end_time)
        }
        self.save_contests()
        return new_id

    def get_contest(self, contest_id):
        return self.contests.get(str(contest_id))

    def get_all_contests(self):
        # Return list sorted by start time (newest first)
        c_list = list(self.contests.values())
        c_list.sort(key=lambda x: x['start_time'], reverse=True)
        return c_list

    def is_running(self, contest_id):
        c = self.get_contest(contest_id)
        if not c: return False
        now = time.time()
        return c['start_time'] <= now <= c['end_time']

    def is_over(self, contest_id):
        c = self.get_contest(contest_id)
        if not c: return False
        return time.time() > c['end_time']
        
    def get_time_remaining(self, contest_id):
        c = self.get_contest(contest_id)
        if not c: return 0
        return max(0, c['end_time'] - time.time())

    # --- Submissions & Leaderboard ---

    def _load_data(self):
        if not os.path.exists(self.data_file):
            return {}
        with open(self.data_file, 'r') as f:
            return json.load(f)

    def _save_data(self, data):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    def get_user_submissions(self, username, contest_id=None):
        data = self._load_data()
        user_subs = data.get(username, [])
        if contest_id:
            # Filter by contest_id
            # Old submissions might not have contest_id, assume "1" or ignore?
            # Let's assume strict filtering.
            return [s for s in user_subs if str(s.get('contest_id')) == str(contest_id)]
        return user_subs

    def save_submission(self, username, contest_id, problem_id, verdict, score):
        data = self._load_data()
        if username not in data:
            data[username] = []
        
        submission = {
            'time': time.strftime('%H:%M:%S'),
            'timestamp': time.time(),
            'contest_id': str(contest_id),
            'problem': problem_id,
            'verdict': verdict,
            'score': score
        }
        data[username].insert(0, submission)
        self._save_data(data)

    def get_leaderboard(self, contest_id, all_users, user_manager=None):
        data = self._load_data()
        leaderboard = []
        contest = self.get_contest(contest_id)
        if not contest: return []

        for user in all_users:
            subs = data.get(user, [])
            best_scores = {} # problem_id -> max_score
            
            for sub in subs:
                # Filter by contest
                if str(sub.get('contest_id')) != str(contest_id):
                    continue
                
                # Check if submission was within contest time (optional, but good for official standings)
                # For now, include all submissions tagged with this contest_id
                
                pid = sub['problem']
                try:
                    score = float(sub.get('score', 0))
                except:
                    score = 0
                    
                if pid not in best_scores:
                    best_scores[pid] = score
                else:
                    best_scores[pid] = max(best_scores[pid], score)
            
            total_score = sum(best_scores.values())
            rating = user_manager.get_rating(user) if user_manager else 0
            
            # Only include if they have participated (score > 0 or submitted?)
            # Usually show everyone who submitted.
            # If no submissions, skip?
            if not best_scores:
                continue

            leaderboard.append({
                'username': user,
                'rating': rating,
                'total_score': int(total_score),
                'breakdown': best_scores
            })
            
        leaderboard.sort(key=lambda x: x['total_score'], reverse=True)
        return leaderboard

    def update_ratings(self, user_manager, contest_id):
        # Get participants
        users = list(user_manager.users.keys())
        leaderboard = self.get_leaderboard(contest_id, users, user_manager)
        
        if not leaderboard: return # No participants
        
        # Extract participants
        participants = [entry['username'] for entry in leaderboard]
        
        # Helper to get entry
        def get_entry(u):
            for e in leaderboard:
                if e['username'] == u: return e
            return None

        # Calculate new ratings (Pairwise Elo)
        new_ratings = {}
        K = 32 # Volatility
        
        # Only update ratings for participants
        for user_a in participants:
            ra = user_manager.get_rating(user_a)
            expected_sum = 0
            actual_sum = 0
            
            for user_b in participants:
                if user_a == user_b: continue
                
                rb = user_manager.get_rating(user_b)
                
                ea = 1 / (1 + 10 ** ((rb - ra) / 400))
                expected_sum += ea
                
                entry_a = get_entry(user_a)
                entry_b = get_entry(user_b)
                
                score_a = entry_a['total_score']
                score_b = entry_b['total_score']
                
                if score_a > score_b:
                    sa = 1.0
                elif score_a < score_b:
                    sa = 0.0
                else:
                    sa = 0.5 # Tie
                
                actual_sum += sa
            
            if len(participants) > 1:
                # Normalize K by number of opponents to prevent massive swings in large contests
                # Standard Elo is 1v1. Here we play N-1 games.
                # A common approach for simple multiplayer Elo is Avg(Actual) - Avg(Expected) * K
                # Or Sum(Actual - Expected) * K / (N-1)
                change = (K * (actual_sum - expected_sum)) / (len(participants) - 1)
                
                # Bonus for participation?
                # change += 1 
            else:
                change = 0

            new_ratings[user_a] = ra + int(change)

        # Apply updates
        for user, rating in new_ratings.items():
            user_manager.users[user]['rating'] = rating
        
        with open(user_manager.users_file, 'w') as f:
            json.dump(user_manager.users, f, indent=4)