
from collections import deque


class StudentNetwork:

    def __init__(self):
        self.graph = {}

    # Add a student to the network
    def add_user(self, user_id):
        if user_id not in self.graph:
            self.graph[user_id] = set()

    # Add an accepted connection
    def add_connection(self, user1, user2):

        if user1 == user2:
            return False

        if user1 not in self.graph or user2 not in self.graph:
            return False

        if user2 in self.graph[user1]:
            return False

        self.graph[user1].add(user2)
        self.graph[user2].add(user1)

        return True

    # Remove an existing connection
    def remove_connection(self, user1, user2):

        if user1 not in self.graph or user2 not in self.graph:
            return False

        if user2 not in self.graph[user1]:
            return False

        self.graph[user1].remove(user2)
        self.graph[user2].remove(user1)

        return True

    # Get all direct connections of a student
    def get_connections(self, user_id):

        if user_id not in self.graph:
            return []

        return list(self.graph[user_id])

    # Find mutual connections between two students
    def mutual_connections(self, user1, user2):

        if user1 not in self.graph or user2 not in self.graph:
            return []

        mutual = self.graph[user1] & self.graph[user2]

        return list(mutual)

    # Find shortest path and degree using BFS
    def shortest_path(self, start, destination):

        if start not in self.graph or destination not in self.graph:
            return None

        if start == destination:
            return [start]

        queue = deque([start])
        visited = {start}
        parent = {start: None}

        while queue:

            current = queue.popleft()

            for neighbour in self.graph[current]:

                if neighbour not in visited:

                    visited.add(neighbour)
                    parent[neighbour] = current

                    if neighbour == destination:

                        path = []
                        node = destination

                        while node is not None:
                            path.append(node)
                            node = parent[node]

                        return path[::-1]

                    queue.append(neighbour)

        return None

    # Find degree of connection
    def connection_degree(self, user1, user2):

        path = self.shortest_path(user1, user2)

        if path is None:
            return -1

        return len(path) - 1

    # Recommend students based on mutual connections
    def people_you_may_know(self, user_id):

        if user_id not in self.graph:
            return []

        suggestions = []

        existing_connections = self.graph[user_id]

        for candidate in self.graph:

            if candidate == user_id:
                continue

            if candidate in existing_connections:
                continue

            mutual_count = len(
                self.graph[user_id] & self.graph[candidate]
            )

            if mutual_count > 0:
                suggestions.append((candidate, mutual_count))

        suggestions.sort(key=lambda x: (-x[1], x[0]))

        return suggestions
