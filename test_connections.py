
from database import Database
from core.graph import StudentNetwork
from core.connections import ConnectionManager

# Create a separate test database
db = Database("connection_test.db")

# Create students
user1 = db.add_user("student_a", "test_hash_a")
user2 = db.add_user("student_b", "test_hash_b")
user3 = db.add_user("student_c", "test_hash_c")

# Load graph from database
network = StudentNetwork()
network.graph = db.load_graph()

# Create database-backed connection manager
manager = ConnectionManager(network, db)

# Send request
print("\n1. Sending request:")
print(manager.send_request(user1, user2))

# Check incoming requests
print("\n2. Incoming requests:")
print(manager.get_incoming_requests(user2))

# Accept request
print("\n3. Accepting request:")
print(manager.accept_request(user2, user1))

# Check graph
print("\n4. Updated graph:")
print(network.graph)

# Check database
print("\n5. Database graph:")
print(db.load_graph())

# Send another request
print("\n6. Sending another request:")
print(manager.send_request(user3, user1))

# Reject request
print("\n7. Rejecting request:")
print(manager.reject_request(user1, user3))

# Remove accepted connection
print("\n8. Removing connection:")
print(manager.remove_connection(user1, user2))

# Verify final graph
print("\n9. Final graph:")
print(network.graph)

print("\n10. Final database graph:")
print(db.load_graph())

db.close()
