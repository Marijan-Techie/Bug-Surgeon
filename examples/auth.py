#!/usr/bin/env python3
"""
Example buggy authentication module for testing Bug Surgeon
This file intentionally contains bugs for testing purposes
"""

from typing import Optional
import sqlite3
from dataclasses import dataclass

@dataclass
class User:
    id: int
    username: str
    email: str

class Session:
    def __init__(self, user_id: int, token: str):
        self.user_id = user_id
        self.token = token

def get_database_connection():
    """Get database connection"""
    return sqlite3.connect('users.db')

def get_session(token: str) -> Optional[Session]:
    """Get session by token"""
    conn = get_database_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM sessions WHERE token = ?", (token,))
    result = cursor.fetchone()

    if result:
        return Session(user_id=result[0], token=token)
    return None

def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user by ID from database"""
    conn = get_database_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        return User(id=result[0], username=result[1], email=result[2])
    return None

def authenticate_user(token: str) -> Optional[int]:
    """
    Authenticate user by token

    BUG: This function has a race condition bug!
    It assumes that if a session exists, the user must exist too.
    But a user could be deleted while their session remains valid.
    """
    session = get_session(token)

    if session:
        # BUG: This line can cause AttributeError if user is None!
        user = get_user_by_id(session.user_id)
        return user.id  # Line 42: 'NoneType' object has no attribute 'id'

    return None

def invalidate_session(session: Session):
    """Remove session from database"""
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (session.token,))
    conn.commit()
    conn.close()

# Example of how the bug manifests:
if __name__ == "__main__":
    # This would cause the AttributeError
    try:
        user_id = authenticate_user("some_valid_token_but_user_deleted")
        print(f"Authenticated user ID: {user_id}")
    except AttributeError as e:
        print(f"Error: {e}")
        print("This is the bug the Bug Surgeon should identify!")
