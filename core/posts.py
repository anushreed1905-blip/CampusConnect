
class PostManager:

    def __init__(self, database):
        self.db = database

    # Create a post
    def create_post(self, user_id, content):

        content = content.strip()

        if not content:
            return False, "Post cannot be empty."

        if len(content) > 1000:
            return False, "Post cannot exceed 1000 characters."

        self.db.create_post(user_id, content)

        return True, "Post published successfully."

    # Get all posts
    def get_feed(self):
        return self.db.get_all_posts()

    # Delete a post
    def delete_post(self, post_id, user_id):

        deleted = self.db.delete_post(post_id, user_id)

        if deleted:
            return True, "Post deleted successfully."

        return False, "Post not found or you cannot delete it."
