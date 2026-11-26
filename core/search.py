class SearchEngine:

    def __init__(self, database):
        self.db = database

    def search_students(self, query, current_user_id):

        query = query.strip().casefold()

        if not query:
            return []

        profiles = self.db.get_all_profiles()

        results = []

        for user_id, profile in profiles.items():

            # Do not display the logged-in student
            if user_id == current_user_id:
                continue

            user = self.db.get_user_by_id(user_id)

            if not user:
                continue

            username = user["username"]
            name = profile.get("full_name") or ""

            username_lower = username.casefold()
            name_lower = name.casefold()

            # Prefix matching
            prefix_match = (
                username_lower.startswith(query)
                or name_lower.startswith(query)
                or any(
                    word.startswith(query)
                    for word in name_lower.split()
                )
            )

            # Partial matching
            partial_match = (
                query in username_lower
                or query in name_lower
            )

            if prefix_match or partial_match:

                student = dict(profile)

                student["user_id"] = user_id
                student["username"] = username
                student["full_name"] = name
                student["prefix_match"] = prefix_match

                results.append(student)

        # Prefix matches appear first
        results.sort(
            key=lambda student: (
                not student["prefix_match"],
                (
                    student["full_name"]
                    or student["username"]
                ).casefold()
            )
        )

        return results