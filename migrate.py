import json
import sys
sys.path.insert(0, "/workspaces/CobbleForces")

from api.data.db import init_db, get_db
from werkzeug.security import generate_password_hash

# Initialize the database
init_db()

# Load users.json
with open("users.json", "r") as f:
    users_json = json.load(f)

conn = get_db()
cursor = conn.cursor()

for username, user_data in users_json.items():
    password = user_data.get("password", "")
    gender = user_data.get("gender")
    is_admin = user_data.get("is_admin", False)
    rating = user_data.get("rating", 0)
    rated_participations = user_data.get("rated_participations", 0)
    
    if not password:
        print(f"⚠️  Skipping {username}: no password found")
        continue
    
    # Check if user already exists
    cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        print(f"✓ {username} already in DB, skipping")
        continue
    
    # Hash and insert
    password_hash = generate_password_hash(password, method="scrypt")
    
    cursor.execute("""
        INSERT INTO users (username, password_hash, gender, is_admin, rating, rated_participations)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, password_hash, gender, 1 if is_admin else 0, rating, rated_participations))
    print(f"✓ Migrated {username}")

conn.commit()
conn.close()
print("\n✅ Migration complete!")