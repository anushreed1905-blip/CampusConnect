
class ConnectionManager:

    def __init__(self, network, database):
        self.network = network
        self.db = database

    # Send a connection request
    def send_request(self, sender, receiver):

        if sender == receiver:
            return False, "You cannot connect with yourself."

        if sender not in self.network.graph:
            return False, "Sender does not exist."

        if receiver not in self.network.graph:
            return False, "Receiver does not exist."

        if receiver in self.network.graph[sender]:
            return False, "Already connected."

        # Check requests in both directions
        incoming = self.db.get_incoming_requests(sender)
        outgoing = self.db.get_outgoing_requests(sender)

        if receiver in outgoing:
            return False, "Request already sent."

        if receiver in incoming:
            return False, "This student has already sent you a request."

        success = self.db.add_request(sender, receiver)

        if not success:
            return False, "Could not send request."

        return True, "Connection request sent."

    # Accept an incoming request
    def accept_request(self, receiver, sender):

        if receiver not in self.network.graph:
            return False, "Receiver does not exist."

        if sender not in self.network.graph:
            return False, "Sender does not exist."

        if sender in self.network.graph[receiver]:
            return False, "Already connected."

        # Save connection and remove request in one transaction
        success = self.db.accept_request(sender, receiver)

        if not success:
            return False, "No pending request found or database error."

        # Update the in-memory graph
        self.network.add_connection(sender, receiver)

        return True, "Connection request accepted."

    # Reject an incoming request
    def reject_request(self, receiver, sender):

        success = self.db.delete_request(sender, receiver)

        if not success:
            return False, "No pending request found."

        return True, "Connection request rejected."

    # Cancel an outgoing request
    def cancel_request(self, sender, receiver):

        success = self.db.delete_request(sender, receiver)

        if not success:
            return False, "No pending request found."

        return True, "Connection request cancelled."

    # Remove an accepted connection
    def remove_connection(self, user1, user2):

        if user1 not in self.network.graph:
            return False, "User does not exist."

        if user2 not in self.network.graph:
            return False, "User does not exist."

        if user2 not in self.network.graph[user1]:
            return False, "Connection does not exist."

        success = self.db.delete_connection(user1, user2)

        if not success:
            return False, "Database could not remove connection."

        # Update the graph after successful database deletion
        self.network.remove_connection(user1, user2)

        return True, "Connection removed."

    # Get incoming requests
    def get_incoming_requests(self, user_id):

        return self.db.get_incoming_requests(user_id)

    # Get outgoing requests
    def get_outgoing_requests(self, user_id):

        return self.db.get_outgoing_requests(user_id)

    # Get all users involved in pending requests
    def get_pending_user_ids(self, user_id):

        pending = set(
            self.get_incoming_requests(user_id)
        )

        pending.update(
            self.get_outgoing_requests(user_id)
        )

        return pending
