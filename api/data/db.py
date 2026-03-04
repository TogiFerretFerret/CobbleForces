import sqlite3
import os
from werkzeug.security import generate_password_hash
DB_PATH = os.path.join(os.path.dirname(__file__), "../../users.db")
def get_db():
    """Returns a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory=sqlite3.Row
    return conn
def init_db():
    """Creates the users table if it doens't exist"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            rating INTEGER NOT NULL DEFAULT 0,
            is_admin INTEGER NOT NULL DEFAULT 0,
            gender TEXT,
            rated_participations INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
def user_exists(username:str)->bool:
    """Checks if a user exists in the database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists
def create_user(username:str, password:str, gender=None, is_admin=False)->bool:
    """Creates a new user in the database with hashed password."""
    if user_exists(username):
        return False
    password_hash = generate_password_hash(password)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (username, password_hash, gender, is_admin, rating, rated_participations)
        VALUES (?, ?, ?, ?, 0, 0)
    """, (username, password_hash, gender, 1 if is_admin else 0))
    conn.commit()
    conn.close()
    return True
def verify_login(username:str, password:str)->None|dict:
    """Check username and password, returning user dict or none"""
    conn = get_db()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return None
    if check_password_hash(user["password_hash"], password):
        return dict(user)
    return None
def get_user(username:str)->None|dict:
    """get user by username without pwd checks (removing the pwd hash)"""
    conn = get_db()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return None
    user_dict = dict(user)
    user_dict.pop("password_hash", None)
    return user_dict
def update_user_rating(username:str, new_rating:int):
    """Update the rating of a user."""
    conn = get_db()
    cursor = conn.cursor()
    if rated_participations is not None:
        cursor.execute("""
            UPDATE users SET rating = ?, rated_participations = ?
            WHERE username = ?
        """, (new_rating, rated_participations, username))
    else:
        cursor.execute("""
            UPDATE users SET rating = ?
            WHERE username = ?
        """, (new_rating, username))
    
    conn.commit()
    conn.close()
def get_all_users():
    """Returns a list of all users in the database (without password hashes)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY rating DESC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    # pop the password hashes from the user dicts
    for user in users:
        user.pop("password_hash", None)
        # tthis increases security not much but makes me feel bette
    return users