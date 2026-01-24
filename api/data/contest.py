import json
import os
import time
import threading

class ContestManager:
    def __init__(self, contests_file='api/data/contests.json', data_file='contest_data.json'):
        self.contests_file = contests_file
        self.data_file = data_file
        self.contests = self._load_contests()
        self.lock = threading.RLock()

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
        c = self.contests.get(str(contest_id))
        if c:
            # Schema migration: Ensure lists exist
            if 'announcements' not in c: c['announcements'] = []
            if 'clarifications' not in c: c['clarifications'] = []
        return c

    def add_announcement(self, contest_id, message):
        c = self.get_contest(contest_id)
        if c:
            c['announcements'].append({
                'message': message,
                'timestamp': time.time()
            })
            self.save_contests()

    def add_clarification(self, contest_id, message):
        c = self.get_contest(contest_id)
        if c:
            c['clarifications'].append({
                'message': message,
                'timestamp': time.time()
            })
            self.save_contests()

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
        with self.lock:
            if not os.path.exists(self.data_file):
                return {}
            with open(self.data_file, 'r') as f:
                data = json.load(f)
        
        # Ensure IDs exist for all submissions
        modified = False
        max_id = 0
        
        # First pass: find max ID
        for user in data:
            for sub in data[user]:
                if 'id' in sub:
                    max_id = max(max_id, sub['id'])
        
        # Second pass: assign missing IDs
        for user in data:
            for sub in data[user]:
                if 'id' not in sub:
                    max_id += 1
                    sub['id'] = max_id
                    modified = True
        
        if modified:
            self._save_data(data)
            
        return data

    def _save_data(self, data):
        # Assumes lock is held by caller if called from _load_data, 
        # but let's make it safe for direct calls too.
        # Use a recursive lock style if needed, or just handle it carefully.
        # Actually, let's just use the lock inside here and make sure callers don't nest.
        # But _load_data calls _save_data... let's use a nested-safe approach.
        # Simplest: check if we already hold the lock? No, threading.Lock isn't reentrant.
        # Let's use threading.RLock instead.
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    def get_user_submissions(self, username, contest_id=None):
        data = self._load_data()
        user_subs = data.get(username, [])
        if contest_id:
            return [s for s in user_subs if str(s.get('contest_id')) == str(contest_id)]
        return user_subs

    def save_submission(self, username, contest_id, problem_id, verdict, score):
        with self.lock:
            data = json.load(open(self.data_file)) if os.path.exists(self.data_file) else {}
            if username not in data:
                data[username] = []
            
            # Calculate sub ID robustly
            max_id = 0
            for user_subs in data.values():
                for s in user_subs:
                    if 'id' in s:
                        max_id = max(max_id, s['id'])
            sub_id = max_id + 1

            submission = {
                'id': sub_id,
                'time': time.strftime('%H:%M:%S'),
                'timestamp': time.time(),
                'contest_id': str(contest_id),
                'problem': problem_id,
                'verdict': verdict,
                'score': score
            }
            data[username].insert(0, submission)
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=4)
        return sub_id

    def get_leaderboard(self, contest_id, all_users, user_manager=None):
        data = self._load_data()
        leaderboard = []
        contest = self.get_contest(contest_id)
        if not contest: return []
        
        start_time = contest['start_time']

        for user in all_users:
            subs = data.get(user, [])
            # Sort subs by timestamp ascending
            subs.sort(key=lambda x: x['timestamp'])
            
            solved_problems = {} # pid -> first_ac_timestamp
            penalties = {} # pid -> number of WAs before AC
            
            for sub in subs:
                if str(sub.get('contest_id')) != str(contest_id):
                    continue
                
                pid = sub['problem']
                if pid in solved_problems:
                    continue
                
                if sub['verdict'] == 'AC':
                    solved_problems[pid] = sub['timestamp']
                else:
                    penalties[pid] = penalties.get(pid, 0) + 1
            
            total_solved = len(solved_problems)
            total_penalty = 0
            breakdown = {} # pid -> {solved: bool, penalty: int, time: int}
            
            for pid, ac_time in solved_problems.items():
                time_taken = int((ac_time - start_time) / 60) # mins
                wa_count = penalties.get(pid, 0)
                total_penalty += time_taken + (wa_count * 20)
                breakdown[pid] = {'solved': True, 'penalty': wa_count, 'time': time_taken}
            
            # Speedster calculation: average penalty per solved problem < 20 mins
            avg_penalty = (total_penalty / total_solved) if total_solved > 0 else 999
            is_speedster = avg_penalty < 20
            
            rating = user_manager.get_rating(user) if user_manager else 0
            
            if not solved_problems and not any(str(s.get('contest_id')) == str(contest_id) for s in subs):
                continue

            leaderboard.append({
                'username': user,
                'rating': rating,
                'total_solved': total_solved,
                'total_penalty': total_penalty,
                'is_speedster': is_speedster,
                'breakdown': breakdown
            })
            
        # Rank by solved (desc) then penalty (asc)
        leaderboard.sort(key=lambda x: (-x['total_solved'], x['total_penalty']))

        # Predict Delta (NQE Logic)
        if leaderboard and user_manager:
            # Assign ranks for delta calculation
            for i, entry in enumerate(leaderboard):
                if i > 0 and leaderboard[i]['total_solved'] == leaderboard[i-1]['total_solved'] and leaderboard[i]['total_penalty'] == leaderboard[i-1]['total_penalty']:
                    entry['actual_rank'] = leaderboard[i-1]['actual_rank']
                else:
                    entry['actual_rank'] = i + 1
            
            # Idempotency: Revert ratings to get effective_rating
            for entry in leaderboard:
                user = entry['username']
                rated_hist = user_manager.get_rated_participations(user)
                current_r = entry['rating']
                if str(contest_id) in rated_hist:
                    old_delta = rated_hist[str(contest_id)]
                    entry['effective_rating'] = current_r - old_delta
                else:
                    entry['effective_rating'] = current_r

            problem_ratings = [800, 1000, 1100, 1700, 2500, 3100, 3500]

            def get_elo_win_probability(ra, rb):
                return 1.0 / (1.0 + 10.0 ** ((rb - ra) / 400.0))

            def get_seed(rating, exclude_user=None):
                seed = 1.0
                for opponent in leaderboard:
                    if opponent['username'] == exclude_user: continue
                    opp_r = opponent.get('effective_rating', opponent['rating'])
                    seed += get_elo_win_probability(opp_r, rating)
                return seed
            
            def find_performance_rating(actual_rank, exclude_user):
                low = 0
                high = 4500
                for _ in range(60):
                    mid = (low + high) / 2
                    if get_seed(mid, exclude_user) < actual_rank:
                        high = mid
                    else:
                        low = mid
                return mid

            for entry in leaderboard:
                user = entry['username']
                effective_rating = entry['effective_rating']
                actual_rank = entry['actual_rank']
                
                # Step 1: Base Performance
                perf_rating = find_performance_rating(actual_rank, user)
                
                # Step 2: Boss Slayer Floor
                solved_indices = []
                for pid, info in entry['breakdown'].items():
                    if info['solved']:
                        try:
                            idx = ord(pid.upper()[0]) - ord('A')
                            if 0 <= idx < len(problem_ratings):
                                solved_indices.append(idx)
                        except:
                            pass
                
                if solved_indices:
                    hardest_idx = max(solved_indices)
                    floor = problem_ratings[hardest_idx] - 200
                    if perf_rating < floor:
                        perf_rating = floor

                # Step 3: Volatility
                rated_hist = user_manager.get_rated_participations(user)
                legacy_count = user_manager.get_participation_count(user)
                current_is_rated = 1 if str(contest_id) in rated_hist else 0
                effective_count = max(len(rated_hist), legacy_count) - current_is_rated
                
                if effective_count < 5:
                    K = 0.8
                elif perf_rating < effective_rating:
                    K = 0.1
                else:
                    K = 0.25
                
                # Step 4: Update & Compression
                raw_delta = K * (perf_rating - effective_rating)
                if effective_rating > 3000 and raw_delta > 0:
                    final_delta = raw_delta * 0.8
                else:
                    final_delta = raw_delta
                
                delta_int = int(round(final_delta))
                new_rating = int(effective_rating + delta_int)
                
                # Delta should be difference from CURRENT rating (what is shown in table)
                # If already rated, this will be 0.
                entry['delta'] = new_rating - entry['rating']

        return leaderboard

    def update_ratings(self, user_manager, contest_id):
        # 1. Get Leaderboard & Participants
        users = list(user_manager.users.keys())
        leaderboard = self.get_leaderboard(contest_id, users, user_manager)
        
        if not leaderboard: return 
        
        # Sort by rank: solved (desc), penalty (asc)
        leaderboard.sort(key=lambda x: (-x['total_solved'], x['total_penalty']))
        
        # Assign Ranks
        for i, entry in enumerate(leaderboard):
            if i > 0 and leaderboard[i]['total_solved'] == leaderboard[i-1]['total_solved'] and leaderboard[i]['total_penalty'] == leaderboard[i-1]['total_penalty']:
                entry['actual_rank'] = leaderboard[i-1]['actual_rank']
            else:
                entry['actual_rank'] = i + 1

        participants = leaderboard
        
        # 2. Prepare Data for Algo
        # Identify Problems (sorted to map to Difficulty Curve)
        # We need all unique problem IDs encountered in this contest to map them to indices 0..6
        all_problem_ids = set()
        for entry in participants:
            for pid in entry['breakdown'].keys():
                all_problem_ids.add(pid)
        sorted_problem_ids = sorted(list(all_problem_ids)) # A, B, C...
        
        problem_ratings = [800, 1000, 1100, 1700, 2500, 3100, 3500]

        # Elo Helpers
        def get_elo_win_probability(ra, rb):
            return 1.0 / (1.0 + 10.0 ** ((rb - ra) / 400.0))

        def get_seed(rating, exclude_user=None):
            seed = 1.0
            for opponent in participants:
                if opponent['username'] == exclude_user: continue
                # Use current effective rating for seed calc
                # (For idempotency, we must use the rating *before* this contest if already rated, 
                # but we handle that by reverting first in the main loop)
                opp_r = opponent.get('effective_rating', opponent['rating'])
                seed += get_elo_win_probability(opp_r, rating)
            return seed

        def find_performance_rating(actual_rank, exclude_user):
            low = 0
            high = 4500
            for _ in range(60):
                mid = (low + high) / 2
                if get_seed(mid, exclude_user) < actual_rank:
                    high = mid
                else:
                    low = mid
            return mid

        # 3. Idempotency Pre-flight
        # We need to temporarily revert ratings for users who have already been rated for this contest
        # to calculate the correct 'Seed' and 'Performance'.
        for entry in participants:
            user = entry['username']
            rated_hist = user_manager.get_rated_participations(user)
            current_r = entry['rating']
            
            if str(contest_id) in rated_hist:
                old_delta = rated_hist[str(contest_id)]
                entry['effective_rating'] = current_r - old_delta
            else:
                entry['effective_rating'] = current_r

        # 4. Calculate New Ratings
        updates = {} # user -> (delta, new_rating)

        for entry in participants:
            user = entry['username']
            effective_rating = entry['effective_rating'] # Rating BEFORE this contest
            actual_rank = entry['actual_rank']
            
            # Step 1: Base Performance
            perf_rating = find_performance_rating(actual_rank, user)
            
            # Step 2: Boss Slayer Floor
            solved_indices = []
            for pid, info in entry['breakdown'].items():
                if info['solved']:
                    try:
                        # Map Letter to Index (A=0, B=1, ..., G=6)
                        # Assumes PID starts with a letter
                        idx = ord(pid.upper()[0]) - ord('A')
                        if 0 <= idx < len(problem_ratings):
                            solved_indices.append(idx)
                    except:
                        pass
            
            if solved_indices:
                hardest_idx = max(solved_indices)
                # Map to problem rating
                floor = problem_ratings[hardest_idx] - 200
                
                # Override: Solving G (idx 6, 3500) guarantees at least 3300 perf
                if perf_rating < floor:
                    perf_rating = floor

            # Step 3: Volatility Selection
            # Use max of new history tracking and legacy counter to avoid resetting veterans to placement mode
            rated_hist = user_manager.get_rated_participations(user)
            legacy_count = user_manager.get_participation_count(user)
            
            # If we are re-rating this contest, don't double count it
            current_is_rated = 1 if str(contest_id) in rated_hist else 0
            
            effective_count = max(len(rated_hist), legacy_count) - current_is_rated
            
            if effective_count < 5:
                K = 0.8 # Placement Mode
            elif perf_rating < effective_rating:
                K = 0.1 # Mercy Mode
            else:
                K = 0.25 # Standard Mode

            # Step 4: Update & Compression
            raw_delta = K * (perf_rating - effective_rating)
            
            # Soft Compression for Enlightened Tiers
            if effective_rating > 3000 and raw_delta > 0:
                final_delta = raw_delta * 0.8
            else:
                final_delta = raw_delta
            
            delta_int = int(round(final_delta))
            new_rating = int(effective_rating + delta_int)
            
            updates[user] = (delta_int, new_rating)

        # 5. Commit Updates
        for user, (delta, new_r) in updates.items():
            user_manager.update_rated_participation(user, contest_id, delta, new_r)