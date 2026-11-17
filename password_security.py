"""Framework-independent password and session service for SCRUM-243.

Python 3.10+, standard library only. Use persistent SQLite DB; connect the
existing app's login, routing and user menu to this service.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

ITERATIONS = 600_000
TOKEN_LIFETIME = 60 * 60 * 8


class AuthenticationError(Exception):
    pass


class PasswordPolicyError(ValueError):
    pass


class ChangeRequiredError(PermissionError):
    pass


class PasswordService:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._initialize()

    @contextmanager
    def _db(self):
        connection = sqlite3.connect(self.db_path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys=ON')
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self):
        with self._db() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS password_users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                must_change_password INTEGER NOT NULL DEFAULT 1 CHECK(must_change_password IN (0,1))
            )''')
            db.execute('''CREATE TABLE IF NOT EXISTS password_sessions (
                token_digest TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES password_users(user_id) ON DELETE CASCADE,
                expires_at INTEGER NOT NULL
            )''')
            db.execute('CREATE INDEX IF NOT EXISTS idx_ps_user ON password_sessions(user_id)')

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
        return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}'

    @staticmethod
    def _verify(password: str, stored: str) -> bool:
        try:
            algorithm, iters, salt, digest = stored.split('$')
            if algorithm != 'pbkdf2_sha256' or not 100_000 <= int(iters) <= 2_000_000:
                return False
            candidate = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), int(iters))
            return hmac.compare_digest(candidate, bytes.fromhex(digest))
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _check_new_password(new_password: str, username: str):
        if not 12 <= len(new_password) <= 128:
            raise PasswordPolicyError('Password must be 12–128 characters long.')
        if username.casefold() in new_password.casefold():
            raise PasswordPolicyError('Password must not include the username.')
        if len(set(new_password)) < 6:
            raise PasswordPolicyError('Password is too repetitive.')

    @staticmethod
    def _digest_token(token: str) -> str:
        return hashlib.sha256(token.encode('ascii')).hexdigest()

    def create_user(self, username: str, temporary_password: str) -> int:
        """Admin/provisioning operation; do not expose to unauthenticated users.

        Deliver the temporary password out of band; never commit real secrets.
        """
        if not re.fullmatch(r'[A-Za-z0-9_.-]{3,64}', username):
            raise ValueError('Username must be 3–64 letters, digits, _, ., or -.')
        if len(temporary_password) < 12:
            raise PasswordPolicyError('Temporary password must be at least 12 characters.')
        with self._db() as db:
            cursor = db.execute('INSERT INTO password_users (username, password_hash, must_change_password) VALUES (?, ?, 1)',
                                (username, self._hash_password(temporary_password)))
            return cursor.lastrowid

    def _issue_session(self, db: sqlite3.Connection, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        db.execute('INSERT INTO password_sessions (token_digest,user_id,expires_at) VALUES (?,?,?)',
                   (self._digest_token(token), user_id, int(time.time()) + TOKEN_LIFETIME))
        return token

    def login(self, username: str, password: str) -> dict:
        """Returns token and `must_change_password` for UI redirect decision.

        Rate-limit at the HTTP/application gateway; use HTTPS in deployment.
        """
        with self._db() as db:
            user = db.execute('SELECT * FROM password_users WHERE username = ?', (username,)).fetchone()
            if user is None or not self._verify(password, user['password_hash']):
                raise AuthenticationError('Invalid username or password.')
            token = self._issue_session(db, user['user_id'])
            return {'token': token, 'user_id': user['user_id'],
                    'must_change_password': bool(user['must_change_password'])}

    def authenticate(self, token: str, *, allow_password_change_only: bool = False) -> dict:
        try:
            digest = self._digest_token(token)
        except (UnicodeEncodeError, AttributeError):
            raise AuthenticationError('Invalid session.') from None
        with self._db() as db:
            user = db.execute('''SELECT u.user_id,u.username,u.must_change_password
                  FROM password_sessions s JOIN password_users u ON u.user_id=s.user_id
                  WHERE s.token_digest=? AND s.expires_at>?''', (digest, int(time.time()))).fetchone()
        if user is None:
            raise AuthenticationError('Invalid or expired session.')
        result = dict(user)
        result['must_change_password'] = bool(result['must_change_password'])
        if result['must_change_password'] and not allow_password_change_only:
            raise ChangeRequiredError('Change your temporary password before continuing.')
        return result

    def change_password(self, token: str, current_password: str, new_password: str) -> str:
        """Requires session and current password. Atomically invalidates ALL
        existing sessions, then returns one fresh token to the caller.
        """
        user = self.authenticate(token, allow_password_change_only=True)
        self._check_new_password(new_password, user['username'])
        with self._db() as db:
            # Serialize concurrent changes and verify token validity again in transaction.
            db.execute('BEGIN IMMEDIATE') if not db.in_transaction else None
            valid = db.execute('''SELECT 1 FROM password_sessions
                 WHERE token_digest=? AND user_id=? AND expires_at>?''',
                 (self._digest_token(token), user['user_id'], int(time.time()))).fetchone()
            row = db.execute('SELECT password_hash FROM password_users WHERE user_id=?',
                             (user['user_id'],)).fetchone()
            if valid is None or row is None:
                raise AuthenticationError('Invalid session.')
            if not self._verify(current_password, row['password_hash']):
                raise AuthenticationError('Current password is incorrect.')
            if self._verify(new_password, row['password_hash']):
                raise PasswordPolicyError('New password must differ from the current password.')
            db.execute('UPDATE password_users SET password_hash=?, must_change_password=0 WHERE user_id=?',
                       (self._hash_password(new_password), user['user_id']))
            db.execute('DELETE FROM password_sessions WHERE user_id=?', (user['user_id'],))
            return self._issue_session(db, user['user_id'])

    def logout(self, token: str) -> None:
        with self._db() as db:
            db.execute('DELETE FROM password_sessions WHERE token_digest=?', (self._digest_token(token),))
