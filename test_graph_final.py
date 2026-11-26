
import unittest
from core.graph import StudentNetwork


class TestCampusConnectGraph(unittest.TestCase):

    def setUp(self):
        self.network = StudentNetwork()

        for user_id in range(1, 7):
            self.network.add_user(user_id)

        # Network: 1 -- 2 -- 3 -- 4
        #                |
        #                5
        # Student 6 is disconnected

        self.network.add_connection(1, 2)
        self.network.add_connection(2, 3)
        self.network.add_connection(3, 4)
        self.network.add_connection(2, 5)

    def test_direct_connection(self):
        self.assertEqual(
            self.network.connection_degree(1, 2), 1
        )

    def test_shortest_path(self):
        self.assertEqual(
            self.network.shortest_path(1, 4),
            [1, 2, 3, 4]
        )

    def test_connection_degree(self):
        self.assertEqual(
            self.network.connection_degree(1, 4), 3
        )

    def test_disconnected_students(self):
        self.assertIsNone(
            self.network.shortest_path(1, 6)
        )
        self.assertEqual(
            self.network.connection_degree(1, 6), -1
        )

    def test_same_student(self):
        self.assertEqual(
            self.network.shortest_path(1, 1), [1]
        )
        self.assertEqual(
            self.network.connection_degree(1, 1), 0
        )

    def test_mutual_connections(self):
        self.assertEqual(
            set(self.network.mutual_connections(1, 3)),
            {2}
        )

    def test_undirected_connection(self):
        self.assertIn(
            1, self.network.get_connections(2)
        )
        self.assertIn(
            2, self.network.get_connections(1)
        )

    def test_duplicate_connection(self):
        self.assertFalse(
            self.network.add_connection(1, 2)
        )

    def test_self_connection(self):
        self.assertFalse(
            self.network.add_connection(1, 1)
        )

    def test_remove_connection(self):
        self.assertTrue(
            self.network.remove_connection(1, 2)
        )
        self.assertNotIn(
            2, self.network.get_connections(1)
        )
        self.assertNotIn(
            1, self.network.get_connections(2)
        )

    def test_recommendations(self):
        suggestions = self.network.people_you_may_know(1)

        suggested_ids = [
            user_id for user_id, count in suggestions
        ]

        self.assertIn(3, suggested_ids)
        self.assertIn(5, suggested_ids)

        self.assertNotIn(1, suggested_ids)
        self.assertNotIn(2, suggested_ids)
        self.assertNotIn(6, suggested_ids)

 
if __name__ == "__main__":
    unittest.main(verbosity=2)
