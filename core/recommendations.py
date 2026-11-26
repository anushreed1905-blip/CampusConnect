
class RecommendationEngine:

    def __init__(self, network, profiles, activity_scores=None):
        self.network = network
        self.profiles = profiles
        self.activity_scores = activity_scores or {}

    def recommend(self, user_id, excluded_users=None, limit=10):

        if user_id not in self.network.graph:
            return []

        excluded_users = set(excluded_users or [])

        current_profile = self.profiles.get(user_id, {})

        current_connections = self.network.graph[user_id]

        current_skills = set(
            current_profile.get("skills", [])
        )

        recommendations = []

        for candidate in self.network.graph:

            # Exclude the current user
            if candidate == user_id:
                continue

            # Exclude existing connections
            if candidate in current_connections:
                continue

            # Exclude users with pending requests
            if candidate in excluded_users:
                continue

            candidate_profile = self.profiles.get(candidate, {})

            # 1. Mutual connections
            mutual_count = len(
                current_connections & self.network.graph[candidate]
            )

            mutual_score = min(mutual_count / 5, 1)

            # 2. Shared skills using Jaccard similarity
            candidate_skills = set(
                candidate_profile.get("skills", [])
            )

            if current_skills or candidate_skills:
                union = current_skills | candidate_skills
                shared = current_skills & candidate_skills
                skill_score = len(shared) / len(union)
            else:
                skill_score = 0

            # 3. Same programme
            same_programme = (
                current_profile.get("programme", "").lower()
                == candidate_profile.get("programme", "").lower()
                and bool(current_profile.get("programme"))
            )

            programme_score = 1 if same_programme else 0

            # 4. Recent activity (value between 0 and 1)
            activity_score = self.activity_scores.get(candidate, 0)
            activity_score = max(0, min(activity_score, 1))

            # 5. Same academic year
            same_year = (
                current_profile.get("study_year")
                == candidate_profile.get("study_year")
                and current_profile.get("study_year") is not None
            )

            year_score = 1 if same_year else 0

            # Final weighted score
            final_score = (
                mutual_score * 40
                + skill_score * 25
                + programme_score * 15
                + activity_score * 15
                + year_score * 5
            )

            # Avoid recommending completely unrelated profiles
            if final_score > 0:

                recommendations.append({
                    "user_id": candidate,
                    "score": round(final_score, 2),
                    "mutual_connections": mutual_count,
                    "shared_skills": list(
                        current_skills & candidate_skills
                    )
                })

        # Highest score first
        recommendations.sort(
            key=lambda x: (-x["score"], x["user_id"])
        )

        return recommendations[:limit]
