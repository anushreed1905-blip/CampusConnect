
from database import Database

db = Database("test_campusconnect.db")

# Register students
user1 = db.add_user("anushree", "dummy_hash_1")
user2 = db.add_user("rahul", "dummy_hash_2")
user3 = db.add_user("priya", "dummy_hash_3")

print("Registered IDs:", user1, user2, user3)

# Save profiles
db.save_profile(
    user1,
    "Anushree",
    "Computer Science",
    2,
    "Interested in AI and technology",
    ["Python", "SQL", "Machine Learning"]
)

db.save_profile(
    user2,
    "Rahul",
    "Computer Science",
    2,
    "Interested in development",
    ["Python", "HTML", "CSS"]
)

db.save_profile(
    user3,
    "Priya",
    "Electronics",
    1,
    "Interested in electronics",
    ["Python", "Arduino"]
)

# Retrieve profile
print("\nAnushree's profile:")
print(db.get_profile(user1))

# Send a connection request
print("\nRequest result:")
print(db.add_request(user1, user2))

# Check incoming requests
print("\nRahul's incoming requests:")
print(db.get_incoming_requests(user2))

# Accept the request in the database
db.add_connection(user1, user2)
db.delete_request(user1, user2)

# Load the graph
print("\nLoaded graph:")
print(db.load_graph())

# Load all profiles
print("\nAll profiles:")
print(db.get_all_profiles())

db.close()
