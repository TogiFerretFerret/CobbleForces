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
