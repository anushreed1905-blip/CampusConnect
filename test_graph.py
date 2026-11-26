from graph import StudentNetwork

network = StudentNetwork()

# Add five students
for student in range(1, 6):
    network.add_user(student)

# Add accepted connections
network.add_connection(1, 2)
network.add_connection(1, 3)
network.add_connection(2, 4)
network.add_connection(3, 4)
network.add_connection(4, 5)

# Display connections
print("Connections of student 1:")
print(network.get_connections(1))

# Find mutual connections
print("\nMutual connections of 2 and 3:")
print(network.mutual_connections(2, 3))

# Find shortest path
print("\nShortest path from 1 to 5:")
print(network.shortest_path(1, 5))

# Find connection degree
print("\nConnection degree:")
print(network.connection_degree(1, 5))

# Find recommendations
print("\nPeople you may know for student 1:")
print(network.people_you_may_know(1))