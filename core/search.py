
class SearchEngine:

    def __init__(self, database):
        self.db = database

    def search_students(self, query, current_user_id):

        query = query.strip().lower()

        if not query:
            return []

        profiles = self.db.get_all_profiles()

        results = []

        # Handle the dictionary returned by get_all_profiles().
        for user_id, profile in profiles.items():

            # Exclude the currently logged-in student.
            if user_id == current_user_id:
                continue

            username = profile.get("username", "").lower()
            full_name = profile.get("full_name", "").lower()

            if query in username or query in full_name:

                results.append({
                    **profile,
                    "user_id": user_id
                })

        return results
