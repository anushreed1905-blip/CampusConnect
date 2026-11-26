
from werkzeug.security import generate_password_hash, check_password_hash


class AccountManager:

    def __init__(self, database):
        self.db = database

    # Register a new student
    def register(self, username, password):

        username = username.strip()

        if not username or not password:
            return False, "Username and password are required."

        if len(username) < 3:
            return False, "Username must have at least 3 characters."

        if len(password) < 8:
            return False, "Password must have at least 8 characters."

        # Convert password into a secure hash
        password_hash = generate_password_hash(password)

        # Save user in database
        user_id = self.db.add_user(username, password_hash)

        if user_id is None:
            return False, "Username already exists."

        # Create an empty profile
        self.db.save_profile(
            user_id,
            username,
            "",
            None,
            "",
            []
        )

        return True, "Account created successfully."

    # Authenticate an existing student
    def login(self, username, password):

        user = self.db.get_user_by_username(username.strip())

        if user is None:
            return None

        # Compare entered password with stored hash
        if check_password_hash(user["password_hash"], password):
            return user["id"]

        return None

    # Update a student's profile
    def update_profile(
        self, user_id, full_name, programme,
        study_year, bio, skills
    ):

        if not full_name.strip():
            return False, "Name cannot be empty."

        self.db.save_profile(
            user_id,
            full_name.strip(),
            programme.strip(),
            study_year,
            bio.strip(),
            skills
        )

        return True, "Profile updated successfully."
