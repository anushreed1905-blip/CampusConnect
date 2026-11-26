import os
import sqlite3
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "campusconnect.db")


class Database:

    def __init__(self, db_name=DB_PATH):

        self.conn = sqlite3.connect(
            db_name,
            check_same_thread=False,
            timeout=30
        )

        self.conn.row_factory = sqlite3.Row

        self.conn.execute("PRAGMA foreign_keys = ON")

        self.create_tables()


    # Create all required tables
    def create_tables(self):

        cursor = self.conn.cursor()

        cursor.executescript("""

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                programme TEXT,
                study_year INTEGER,
                bio TEXT,
                skills TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS connection_requests (
                sender_id INTEGER,
                receiver_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(sender_id, receiver_id),
                FOREIGN KEY(sender_id) REFERENCES users(id)
                ON DELETE CASCADE,
                FOREIGN KEY(receiver_id) REFERENCES users(id)
                ON DELETE CASCADE,
                CHECK(sender_id != receiver_id)
            );

            CREATE TABLE IF NOT EXISTS connections (
                user_low INTEGER,
                user_high INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(user_low, user_high),
                FOREIGN KEY(user_low) REFERENCES users(id)
                ON DELETE CASCADE,
                FOREIGN KEY(user_high) REFERENCES users(id)
                ON DELETE CASCADE,
                CHECK(user_low < user_high)
            );

            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
            );

        """)

        self.conn.commit()

    # Register a new user
    def add_user(self, username, password_hash):

        try:

            cursor = self.conn.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
                """,
                (username, password_hash)
            )

            self.conn.commit()

            return cursor.lastrowid

        except sqlite3.IntegrityError:
            return None

    # Find user using username
    def get_user_by_username(self, username):

        cursor = self.conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )

        return cursor.fetchone()

    # Find user using ID
    def get_user_by_id(self, user_id):

        cursor = self.conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )

        return cursor.fetchone()

    # Save or update a student profile
    def save_profile(
        self, user_id, full_name, programme,
        study_year, bio, skills
    ):

        skills_json = json.dumps(skills)

        self.conn.execute(
            """
            INSERT INTO profiles
            (user_id, full_name, programme, study_year, bio, skills)
            VALUES (?, ?, ?, ?, ?, ?)

            ON CONFLICT(user_id) DO UPDATE SET
                full_name = excluded.full_name,
                programme = excluded.programme,
                study_year = excluded.study_year,
                bio = excluded.bio,
                skills = excluded.skills
            """,
            (
                user_id, full_name, programme,
                study_year, bio, skills_json
            )
        )

        self.conn.commit()

    # Get one student's profile
    def get_profile(self, user_id):

        cursor = self.conn.execute(
            "SELECT * FROM profiles WHERE user_id = ?",
            (user_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return {}

        profile = dict(row)
        profile["skills"] = json.loads(profile["skills"] or "[]")

        return profile

    # Get all student profiles
    def get_all_profiles(self):

        cursor = self.conn.execute(
            "SELECT * FROM profiles"
        )

        profiles = {}

        for row in cursor.fetchall():

            profile = dict(row)

            profile["skills"] = json.loads(
                profile["skills"] or "[]"
            )

            profiles[profile["user_id"]] = profile

        return profiles

    # Save a pending connection request
    def add_request(self, sender, receiver):

        try:

            self.conn.execute(
                """
                INSERT INTO connection_requests
                (sender_id, receiver_id)
                VALUES (?, ?)
                """,
                (sender, receiver)
            )

            self.conn.commit()
            return True

        except sqlite3.IntegrityError:
            return False

    # Delete a pending request
    def delete_request(self, sender, receiver):

        cursor = self.conn.execute(
            """
            DELETE FROM connection_requests
            WHERE sender_id = ? AND receiver_id = ?
            """,
            (sender, receiver)
        )

        self.conn.commit()

        return cursor.rowcount > 0

    # Get incoming requests
    def get_incoming_requests(self, user_id):

        cursor = self.conn.execute(
            """
            SELECT sender_id
            FROM connection_requests
            WHERE receiver_id = ?
            """,
            (user_id,)
        )

        return [row["sender_id"] for row in cursor.fetchall()]

    # Get outgoing requests
    def get_outgoing_requests(self, user_id):

        cursor = self.conn.execute(
            """
            SELECT receiver_id
            FROM connection_requests
            WHERE sender_id = ?
            """,
            (user_id,)
        )

        return [row["receiver_id"] for row in cursor.fetchall()]

    # Save an accepted connection
    def add_connection(self, user1, user2):

        low, high = sorted((user1, user2))

        try:

            self.conn.execute(
                """
                INSERT INTO connections (user_low, user_high)
                VALUES (?, ?)
                """,
                (low, high)
            )

            self.conn.commit()
            return True

        except sqlite3.IntegrityError:
            return False

    # Remove an accepted connection
    def delete_connection(self, user1, user2):

        low, high = sorted((user1, user2))

        cursor = self.conn.execute(
            """
            DELETE FROM connections
            WHERE user_low = ? AND user_high = ?
            """,
            (low, high)
        )

        self.conn.commit()

        return cursor.rowcount > 0

    # Load all accepted connections into the graph
    def load_graph(self):

        cursor = self.conn.execute(
            "SELECT user_low, user_high FROM connections"
        )

        graph = {}

        # Include every registered student
        users = self.conn.execute(
            "SELECT id FROM users"
        ).fetchall()

        for user in users:
            graph[user["id"]] = set()

        # Add both directions for each accepted connection
        for row in cursor.fetchall():

            user1 = row["user_low"]
            user2 = row["user_high"]

            graph[user1].add(user2)
            graph[user2].add(user1)

        return graph

    # Close the database connection
    def close(self):

        self.conn.close()

    # Accept a request and save the connection as one transaction
    def accept_request(self, sender, receiver):

        try:
            self.conn.execute("BEGIN")

            # Check whether the request actually exists
            cursor = self.conn.execute(
                """
                SELECT * FROM connection_requests
                WHERE sender_id = ? AND receiver_id = ?
                """,
                (sender, receiver)
            )

            if cursor.fetchone() is None:
                self.conn.rollback()
                return False

            # Store the connection in canonical order
            low, high = sorted((sender, receiver))

            self.conn.execute(
                """
                INSERT INTO connections (user_low, user_high)
                VALUES (?, ?)
                """,
                (low, high)
            )

            # Delete the pending request
            self.conn.execute(
                """
                DELETE FROM connection_requests
                WHERE sender_id = ? AND receiver_id = ?
                """,
                (sender, receiver)
            )

            self.conn.commit()
            return True

        except sqlite3.Error:
            self.conn.rollback()
            return False

    def search_students(self, search_text, current_user_id):

        search_pattern = f"%{search_text}%"

        cursor = self.conn.execute(
            """
            SELECT
                users.id AS user_id,
                users.username,
                profiles.full_name,
                profiles.programme,
                profiles.study_year,
                profiles.bio,
                profiles.skills

            FROM users

            LEFT JOIN profiles
            ON users.id = profiles.user_id

            WHERE users.id != ?
            AND (
                users.username LIKE ?
                OR profiles.full_name LIKE ?
            )

            ORDER BY profiles.full_name COLLATE NOCASE,
                    users.username COLLATE NOCASE
            """,
            (current_user_id, search_pattern, search_pattern)
        )

        results = []

        for row in cursor.fetchall():

            student = dict(row)

            # Convert the stored JSON skills into a Python list.
            student["skills"] = json.loads(
                student["skills"] or "[]"
            )

            results.append(student)

        return results

    # Create a new post
    def create_post(self, user_id, content):
        cursor = self.conn.execute(
            """
            INSERT INTO posts (user_id, content, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, content)
        )

        self.conn.commit()
        return cursor.lastrowid

    def get_feed_posts(self, allowed_user_ids):

        allowed_user_ids = set(allowed_user_ids)

        rows = self.conn.execute("""
            SELECT
                posts.id AS post_id,
                posts.user_id,
                posts.content,
                posts.created_at,
                users.username,
                profiles.full_name

            FROM posts

            JOIN users
                ON posts.user_id = users.id

            LEFT JOIN profiles
                ON profiles.user_id = users.id

        """).fetchall()

        posts = []

        for row in rows:

            post = dict(row)

            # Only include permitted authors
            if post["user_id"] in allowed_user_ids:

                posts.append(post)

        # Arrange posts from newest to oldest
        posts.sort(
            key=lambda post: (
                post["created_at"],
                post["post_id"]
            ),
            reverse=True
        )

        return posts[:100]

    # Delete a post only if it belongs to the requesting user
    def delete_post(self, post_id, user_id):
        cursor = self.conn.execute(
            """
            DELETE FROM posts
            WHERE id = ? AND user_id = ?
            """,
            (post_id, user_id)
        )

        self.conn.commit()
        return cursor.rowcount > 0

    def create_social_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS post_likes (
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (post_id, user_id),
                FOREIGN KEY (post_id) REFERENCES posts(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS post_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            );
        """)
        self.conn.commit()

    def toggle_post_like(self, post_id, user_id):
        post = self.conn.execute(
            "SELECT id FROM posts WHERE id = ?", (post_id,)
        ).fetchone()

        if post is None:
            return False

        existing = self.conn.execute(
            """SELECT 1 FROM post_likes
               WHERE post_id = ? AND user_id = ?""",
            (post_id, user_id)
        ).fetchone()

        if existing:
            self.conn.execute(
                "DELETE FROM post_likes WHERE post_id = ? AND user_id = ?",
                (post_id, user_id)
            )
        else:
            self.conn.execute(
                "INSERT INTO post_likes (post_id, user_id) VALUES (?, ?)",
                (post_id, user_id)
            )

        self.conn.commit()
        return True

    def add_post_comment(self, post_id, user_id, content):
        post = self.conn.execute(
            "SELECT id FROM posts WHERE id = ?", (post_id,)
        ).fetchone()

        if post is None:
            return False

        self.conn.execute(
            """INSERT INTO post_comments (post_id, user_id, content)
               VALUES (?, ?, ?)""",
            (post_id, user_id, content)
        )
        self.conn.commit()
        return True

    def delete_post_comment(self, comment_id, user_id):
        cursor = self.conn.execute(
            """DELETE FROM post_comments
               WHERE id = ? AND user_id = ?""",
            (comment_id, user_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def get_post_likes(self, post_id):
        row = self.conn.execute(
            "SELECT COUNT(*) AS count FROM post_likes WHERE post_id = ?",
            (post_id,)
        ).fetchone()
        return row["count"]

    def has_liked_post(self, post_id, user_id):
        row = self.conn.execute(
            """SELECT 1 FROM post_likes
               WHERE post_id = ? AND user_id = ?""",
            (post_id, user_id)
        ).fetchone()
        return row is not None

    def get_post_comments(self, post_id):
        rows = self.conn.execute(
            """
            SELECT
                c.id AS comment_id,
                c.user_id,
                c.content,
                c.created_at,
                u.username,
                p.full_name
            FROM post_comments AS c
            JOIN users AS u ON c.user_id = u.id
            LEFT JOIN profiles AS p ON c.user_id = p.user_id
            WHERE c.post_id = ?
            ORDER BY c.created_at ASC, c.id ASC
            """,
            (post_id,)
        ).fetchall()

        return [dict(row) for row in rows]
