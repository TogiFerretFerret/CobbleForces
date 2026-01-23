import json
import os

class UserManager:
    def __init__(self, users_file='users.json'):
        self.users_file = users_file
        self.users = self._load_users()

    def _load_users(self):
        if not os.path.exists(self.users_file):
            return {}
        with open(self.users_file, 'r') as f:
            return json.load(f)

    def validate_login(self, username, password):
        if username in self.users:
            if self.users[username]['password'] == password:
                return True
        return False

    def get_rating(self, username):
        return self.users.get(username, {}).get('rating', 0)

    def get_gender(self, username):
        return self.users.get(username, {}).get('gender', 'Male')

    def is_admin(self, username):
        return self.users.get(username, {}).get('is_admin', False)

    def get_participation_count(self, username):
        return self.users.get(username, {}).get('contests_participated', 0)

    def get_rated_participations(self, username):
        return self.users.get(username, {}).get('rated_participations', {})

    def update_rated_participation(self, username, contest_id, delta, new_rating):
        if username not in self.users: return
        
        if 'rated_participations' not in self.users[username]:
            self.users[username]['rated_participations'] = {}
            
        self.users[username]['rated_participations'][str(contest_id)] = delta
        self.users[username]['rating'] = new_rating
        # Update contest count based on unique rated contests
        self.users[username]['contests_participated'] = len(self.users[username]['rated_participations'])
        self.save_users()

    def save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=4)

    def increment_participation(self, username):
        # Deprecated in favor of update_rated_participation logic, but kept for compatibility if needed
        pass
