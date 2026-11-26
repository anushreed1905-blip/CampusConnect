
from database import Database
from core.accounts import AccountManager

db = Database("accounts_test.db")

accounts = AccountManager(db)

# Register
print(accounts.register("anushree", "password123"))

# Try duplicate registration
print(accounts.register("anushree", "another123"))

# Correct login
user_id = accounts.login("anushree", "password123")
print("Login ID:", user_id)

# Incorrect login
print("Wrong password:", accounts.login("anushree", "wrong123"))

# Update profile
if user_id:
    print(
        accounts.update_profile(
            user_id,
            "Anushree",
            "Computer Science",
            2,
            "Interested in technology",
            ["Python", "SQL", "Machine Learning"]
        )
    )

    print("Saved profile:")
    print(db.get_profile(user_id))

db.close()
