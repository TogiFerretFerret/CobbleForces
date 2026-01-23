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
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    def get_user_submissions(self, username, contest_id=None):
        data = self._load_data()
        user_subs = data.get(username, [])
        if contest_id:
            return [s for s in user_subs if str(s.get('contest_id')) == str(contest_id)]
        return user_subs

    def save_submission(self, username, contest_id, problem_id, verdict, score):
        data = self._load_data()
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
        self._save_data(data)
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
        if leaderboard:
            # Assign ranks for delta calculation
            for i, entry in enumerate(leaderboard):
                if i > 0 and leaderboard[i]['total_solved'] == leaderboard[i-1]['total_solved'] and leaderboard[i]['total_penalty'] == leaderboard[i-1]['total_penalty']:
                    entry['actual_rank'] = leaderboard[i-1]['actual_rank']
                else:
                    entry['actual_rank'] = i + 1

            for entry in leaderboard:
                user = entry['username']
                curr = entry['rating']
                rank = entry['actual_rank']
                
                def prob(ra, rb): return 1 / (1 + 10 ** ((rb - ra) / 400))
                def get_seed(r, exc):
                    s = 1.0
                    for opp in leaderboard:
                        if opp['username'] == exc: continue
                        s += prob(opp['rating'], r)
                    return s
                
                low, high = 0, 8000
                for _ in range(40):
                    mid = (low + high) / 2
                    if get_seed(mid, user) < rank: high = mid
                    else: low = mid
                
                perf = mid
                p_count = user_manager.get_participation_count(user) if user_manager else 0
                k = 0.5 if p_count <= 10 else 0.2
                if perf < curr: k /= 2
                
                raw_change = k * (perf - curr)
                # Protagonist bonus: if solved at least one
                bonus = 5 if (curr < 1200 and entry['total_solved'] > 0) else 0
                # Speedster bonus: if avg penalty < 20 mins
                if entry['is_speedster']:
                    bonus += 2
                
                change = raw_change + bonus
                
                new_r = curr + change
                if new_r > 4000: new_r = 4000 + (new_r - 4000) / 2
                
                entry['delta'] = int(round(new_r - curr))

        return leaderboard

    def update_ratings(self, user_manager, contest_id):
        # Get participants
        users = list(user_manager.users.keys())
        leaderboard = self.get_leaderboard(contest_id, users, user_manager)
        
        if not leaderboard: return # No participants
        
        # Rank by solved (desc) then penalty (asc)
        leaderboard.sort(key=lambda x: (-x['total_solved'], x['total_penalty']))
        for i, entry in enumerate(leaderboard):
            if i > 0 and leaderboard[i]['total_solved'] == leaderboard[i-1]['total_solved'] and leaderboard[i]['total_penalty'] == leaderboard[i-1]['total_penalty']:
                entry['actual_rank'] = leaderboard[i-1]['actual_rank']
            else:
                entry['actual_rank'] = i + 1

        participants = leaderboard
        num_participants = len(participants)
        
        def get_elo_win_probability(ra, rb):
            return 1 / (1 + 10 ** ((rb - ra) / 400))

        def get_seed(rating, exclude_user=None):
            seed = 1.0
            for opponent in participants:
                if opponent['username'] == exclude_user: continue
                seed += get_elo_win_probability(opponent['rating'], rating)
            return seed

        def find_performance_rating(actual_rank, exclude_user):
            low = 0
            high = 8000
            for _ in range(100):
                mid = (low + high) / 2
                if get_seed(mid, exclude_user) < actual_rank:
                    high = mid
                else:
                    low = mid
            return mid

        # Get all contests sorted by time to check streaks
        all_contests = self.get_all_contests()
        all_contests.sort(key=lambda x: x['start_time'])
        contest_ids_sorted = [c['id'] for c in all_contests]
        
        try:
            current_idx = contest_ids_sorted.index(str(contest_id))
            last_3_ids = contest_ids_sorted[max(0, current_idx-2):current_idx+1]
        except:
            last_3_ids = [str(contest_id)]

        new_ratings = {}
        for entry in participants:
            user = entry['username']
            current_rating = entry['rating']
            actual_rank = entry['actual_rank']
            
            performance_rating = find_performance_rating(actual_rank, user)
            
            participation_count = user_manager.get_participation_count(user)
            k = 0.5 if participation_count <= 10 else 0.2
            if performance_rating < current_rating:
                k /= 2
            
            raw_change = k * (performance_rating - current_rating)
            
            bonus = 0
            if current_rating < 1200 and entry['total_solved'] > 0:
                bonus += 5
            
            # Speedster bonus
            if entry['is_speedster']:
                bonus += 2
            
            participated_in_last_3 = True
            if len(last_3_ids) < 3:
                participated_in_last_3 = False
            else:
                submission_data = self._load_data()
                for cid in last_3_ids:
                    user_subs = submission_data.get(user, [])
                    if not any(str(s.get('contest_id')) == str(cid) for s in user_subs):
                        participated_in_last_3 = False
                        break
            
            change = raw_change + bonus
            if participated_in_last_3:
                change *= 1.1
            
            new_rating = current_rating + change
            if new_rating > 4000:
                new_rating = 4000 + (new_rating - 4000) / 2
            
            new_ratings[user] = int(round(new_rating))
            user_manager.increment_participation(user)

        # Apply updates
        for user, rating in new_ratings.items():
            user_manager.users[user]['rating'] = rating
        
        user_manager.save_users()