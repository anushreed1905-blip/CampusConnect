
from database import Database
from core.graph import StudentNetwork
from core.recommendations import RecommendationEngine
from core.connections import ConnectionManager

db = Database("connection_test.db")

# Load the actual student network
network = StudentNetwork()
network.graph = db.load_graph()

# Load actual student profiles
profiles = db.get_all_profiles()

# Create connection manager
manager = ConnectionManager(network, db)

# Create recommendation engine
activity_scores = {}

engine = RecommendationEngine(
    network,
    profiles,
    activity_scores
)

# Choose the logged-in student
current_user_id = 1

# Exclude pending requests
pending = manager.get_pending_user_ids(current_user_id)

# Generate recommendations
results = engine.recommend(
    current_user_id,
    excluded_users=pending
)

print("\nPeople you may know:")

for result in results:
    print(result)

db.close()
