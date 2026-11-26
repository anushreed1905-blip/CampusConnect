
from importlib.resources import path

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash , jsonify
)
from streamlit import user

from database import Database
from core.graph import StudentNetwork
from core.accounts import AccountManager
from core.connections import ConnectionManager
from core.recommendations import RecommendationEngine
from core.search import SearchEngine
from core.posts import PostManager

# --------------------------------------------------
# 1. FLASK APPLICATION SETUP
# --------------------------------------------------

app = Flask(__name__)

# Used by Flask to securely manage sessions.
# Replace this with a long random secret before deployment.
app.secret_key = "campusconnect-development-secret"


# --------------------------------------------------
# 2. INITIALIZE PROJECT MODULES
# --------------------------------------------------

db = Database()

db.create_social_tables()
network = StudentNetwork()
network.graph = db.load_graph()

account_manager = AccountManager(db)
connection_manager = ConnectionManager(network, db)
search_engine = SearchEngine(db)
post_manager = PostManager(db)

# --------------------------------------------------
# 3. HELPER FUNCTIONS
# --------------------------------------------------

def login_required():
    """Check whether a student is logged in."""
    return "user_id" in session


def refresh_network():
    """Reload accepted connections from the database."""
    network.graph = db.load_graph()


def get_current_user():
    """Retrieve the logged-in student's database record."""
    if not login_required():
        return None

    return db.get_user_by_id(session["user_id"])


# --------------------------------------------------
# 4. HOME PAGE
# --------------------------------------------------

@app.route("/")
def home():
    if login_required():
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# --------------------------------------------------
# 5. STUDENT REGISTRATION
# --------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        success, message = account_manager.register(
            username,
            password
        )

        if success:
            flash(message, "success")
            return redirect(url_for("login"))

        flash(message, "error")

    return render_template("signup.html")


# --------------------------------------------------
# 6. STUDENT LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user_id = account_manager.login(username, password)

        if user_id is not None:

            session.clear()
            session["user_id"] = user_id

            flash("Login successful!", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


# --------------------------------------------------
# 7. STUDENT LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("login"))


# --------------------------------------------------
# 8. STUDENT DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():

    if not login_required():
        return redirect(url_for("login"))

    # Get the currently logged-in student's ID
    user_id = session["user_id"]
    user = db.get_user_by_id(user_id)

    if user is None:
        session.clear()
        flash("Please log in again.")
        return redirect(url_for("login"))

    # Get the logged-in student's account and profile
    user = get_current_user()
    current_profile = db.get_profile(user_id)

    # ------------------------------------------
    # ACCEPTED CONNECTIONS
    # ------------------------------------------

    connection_ids = network.get_connections(user_id)

    connected_students = []

    for connected_id in connection_ids:

        connected_profile = db.get_profile(connected_id)

        if connected_profile:
            connected_students.append(connected_profile)

    # ------------------------------------------
    # INCOMING CONNECTION REQUESTS
    # ------------------------------------------

    incoming_ids = db.get_incoming_requests(user_id)

    incoming_requests = []

    for sender_id in incoming_ids:

        sender = db.get_user_by_id(sender_id)
        sender_profile = db.get_profile(sender_id)

        if sender:
            incoming_requests.append({
                "sender_id": sender_id,
                "username": sender["username"],
                "full_name": (
                    sender_profile["full_name"]
                    if sender_profile
                    else sender["username"]
                )
            })

    # ------------------------------------------
    # OUTGOING CONNECTION REQUESTS
    # ------------------------------------------

    outgoing_ids = db.get_outgoing_requests(user_id)

    outgoing_requests = []

    for receiver_id in outgoing_ids:

        receiver = db.get_user_by_id(receiver_id)
        receiver_profile = db.get_profile(receiver_id)

        if receiver:
            outgoing_requests.append({
                "receiver_id": receiver_id,
                "username": receiver["username"],
                "full_name": (
                    receiver_profile["full_name"]
                    if receiver_profile
                    else receiver["username"]
                )
            })

    # ------------------------------------------
    # STUDENT RECOMMENDATIONS
    # ------------------------------------------

    refresh_network()

    profiles = db.get_all_profiles()

    recommendation_engine = RecommendationEngine(
        network,
        profiles,
        activity_scores={}
    )

    pending_ids = connection_manager.get_pending_user_ids(user_id)

    recommended_results = recommendation_engine.recommend(
        user_id,
        excluded_users=pending_ids
    )

    recommendations = []

    for result in recommended_results:

        student_profile = db.get_profile(result["user_id"])

        if student_profile:
            recommendations.append({
                **result,
                **student_profile
            })

    # ------------------------------------------
    # RENDER DASHBOARD
    # ------------------------------------------
    
    # Prepare feed with likes and comments
    feed_posts = post_manager.get_feed()

    for post in feed_posts:
        post_id = post["post_id"]

        post["like_count"] = db.get_post_likes(post_id)

        post["liked_by_me"] = db.has_liked_post(
            post_id,
            user_id
        )

        post["comments"] = db.get_post_comments(post_id)

    return render_template(
        "dashboard.html",
        user=user,
        profile=current_profile,
        connected_students=connected_students,
        incoming_requests=incoming_requests,
        outgoing_requests=outgoing_requests,
        recommendations=recommendations,
        posts=feed_posts
    )

# --------------------------------------------------
# 9. VIEW AND UPDATE PROFILE
# --------------------------------------------------

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if request.method == "POST":

        full_name = request.form.get("full_name", "")
        programme = request.form.get("programme", "")
        study_year = request.form.get("study_year", "")
        bio = request.form.get("bio", "")

        # Convert comma-separated skills into a Python list.
        skills_text = request.form.get("skills", "")

        skills = [
            skill.strip()
            for skill in skills_text.split(",")
            if skill.strip()
        ]

        # Convert the year into an integer if provided.
        try:
            study_year = int(study_year) if study_year else None
        except ValueError:
            flash("Please enter a valid study year.", "error")
            return redirect(url_for("profile"))

        success, message = account_manager.update_profile(
            user_id,
            full_name,
            programme,
            study_year,
            bio,
            skills
        )

        flash(message, "success" if success else "error")

        return redirect(url_for("profile"))

    profile_data = db.get_profile(user_id)

    return render_template(
        "profile.html",
        profile=profile_data
    )


# --------------------------------------------------
# 10. SEND CONNECTION REQUEST
# --------------------------------------------------

@app.route("/connect/<int:receiver_id>", methods=["POST"])
def send_connection_request(receiver_id):

    if not login_required():
        return redirect(url_for("login"))

    sender_id = session["user_id"]

    success, message = connection_manager.send_request(
        sender_id,
        receiver_id
    )

    flash(message, "success" if success else "error")

    return redirect(url_for("dashboard"))


# --------------------------------------------------
# 11. ACCEPT CONNECTION REQUEST
# --------------------------------------------------

@app.route("/accept/<int:sender_id>", methods=["POST"])
def accept_connection_request(sender_id):

    if not login_required():
        return redirect(url_for("login"))

    receiver_id = session["user_id"]

    success, message = connection_manager.accept_request(
        receiver_id,
        sender_id
    )

    refresh_network()

    flash(message, "success" if success else "error")

    return redirect(url_for("dashboard"))


# --------------------------------------------------
# 12. REJECT CONNECTION REQUEST
# --------------------------------------------------

@app.route("/reject/<int:sender_id>", methods=["POST"])
def reject_connection_request(sender_id):

    if not login_required():
        return redirect(url_for("login"))

    receiver_id = session["user_id"]

    success, message = connection_manager.reject_request(
        receiver_id,
        sender_id
    )

    flash(message, "success" if success else "error")

    return redirect(url_for("dashboard"))


# --------------------------------------------------
# 13. CANCEL OUTGOING REQUEST
# --------------------------------------------------

@app.route("/cancel/<int:receiver_id>", methods=["POST"])
def cancel_connection_request(receiver_id):

    if not login_required():
        return redirect(url_for("login"))

    sender_id = session["user_id"]

    success, message = connection_manager.cancel_request(
        sender_id,
        receiver_id
    )

    flash(message, "success" if success else "error")

    return redirect(url_for("dashboard"))


# --------------------------------------------------
# 14. REMOVE AN ACCEPTED CONNECTION
# --------------------------------------------------

@app.route("/remove/<int:other_user_id>", methods=["POST"])
def remove_connection(other_user_id):

    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    success, message = connection_manager.remove_connection(
        user_id,
        other_user_id
    )

    refresh_network()

    flash(message, "success" if success else "error")

    return redirect(url_for("dashboard"))


# --------------------------------------------------
# MUTUAL CONNECTIONS
# --------------------------------------------------

@app.route("/mutual-connections/<int:other_user_id>")
def mutual_connections(other_user_id):

    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if user_id == other_user_id:
        flash("Select another student.")
        return redirect(url_for("dashboard"))

    other_user = db.get_user_by_id(other_user_id)

    if other_user is None:
        flash("Student not found.")
        return redirect(url_for("dashboard"))

    refresh_network()

    mutual_ids = network.mutual_connections(
        user_id, other_user_id
    )
    path = network.shortest_path(user_id, other_user_id)

    degree = -1 if path is None else len(path) - 1

    mutual_students = []

    for student_id in sorted(mutual_ids):
        student = db.get_user_by_id(student_id)
        student_profile = db.get_profile(student_id)

        if student:
            mutual_students.append({
                "user_id": student_id,
                "username": student["username"],
                "full_name": (
                    student_profile["full_name"]
                    if student_profile and student_profile["full_name"]
                    else student["username"]
                ),
                "programme": (
                    student_profile["programme"]
                    if student_profile
                    else ""
                )
            })

    other_profile = db.get_profile(other_user_id)

    return render_template(
        "mutual_connections.html",
        other_user=other_user,
        other_profile=other_profile,
        mutual_students=mutual_students,
        degree=degree
    )


# --------------------------------------------------
# BFS SHORTEST CONNECTION PATH
# --------------------------------------------------


@app.route("/connection-path/<int:other_user_id>")
def connection_path(other_user_id):

    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    other_user = db.get_user_by_id(other_user_id)

    if other_user is None:
        flash("Student not found.")
        return redirect(url_for("dashboard"))

    refresh_network()

    path = network.shortest_path(user_id, other_user_id)

    degree = -1 if path is None else len(path) - 1

    path_students = []

    if path is not None:
        for student_id in path:

            student = db.get_user_by_id(student_id)
            student_profile = db.get_profile(student_id)

            if student is None:
                continue

            full_name = (
                student_profile["full_name"]
                if student_profile and student_profile["full_name"]
                else student["username"]
            )

            path_students.append({
                "user_id": student_id,
                "username": student["username"],
                "full_name": full_name
            })

    return render_template(
        "connections.html",
        other_user=other_user,
        path_students=path_students,
        degree=degree
    )




# --------------------------------------------------
# SEARCH STUDENTS
# --------------------------------------------------

@app.route("/search", methods=["GET", "POST"])
def search():

    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        query = request.form.get("query", "").strip()
    else:
        query = request.args.get("q", "").strip()

    results = []

    if query:
        results = search_engine.search_students(
            query,
            session["user_id"]
        )

        refresh_network()

        current_id = session["user_id"]

        pending_ids = set(
            connection_manager.get_pending_user_ids(current_id)
        )

        connected_ids = set(
            network.get_connections(current_id)
        )

        for student in results:
            student_id = student["user_id"]

            path = network.shortest_path(
                current_id,
                student_id
            )

            student["degree"] = len(path) - 1 if path else -1
            student["connected"] = student_id in connected_ids
            student["pending"] = student_id in pending_ids

    return render_template(
        "search.html",
        results=results,
        query=query
    )


# --------------------------------------------------
# LIVE STUDENT SEARCH SUGGESTIONS
# --------------------------------------------------

@app.route("/search/suggest")
def search_suggest():

    if not login_required():
        return jsonify([]), 401

    query = request.args.get("q", "").strip()

    if not query:
        return jsonify([])

    matches = search_engine.search_students(
        query,
        session["user_id"]
    )

    suggestions = []

    for student in matches[:8]:
        suggestions.append({
            "username": student["username"],
            "name": student.get("full_name") or student["username"]
        })

    return jsonify(suggestions)


# Create a new post
@app.route("/post/create", methods=["POST"])
def create_post():

    if not login_required():
        return redirect(url_for("login"))

    content = request.form.get("content", "")

    success, message = post_manager.create_post(
        session["user_id"],
        content
    )

    flash(message)

    return redirect(url_for("dashboard"))


# Delete a post
@app.route("/post/delete/<int:post_id>", methods=["POST"])
def delete_post(post_id):

    if not login_required():
        return redirect(url_for("login"))

    success, message = post_manager.delete_post(
        post_id,
        session["user_id"]
    )

    flash(message)

    return redirect(url_for("dashboard"))


# --------------------------------------------------
# POST LIKES
# --------------------------------------------------

@app.route("/post/<int:post_id>/like", methods=["POST"])
def like_post(post_id):

    if not login_required():
        return redirect(url_for("login"))

    success = db.toggle_post_like(
        post_id,
        session["user_id"]
    )

    if not success:
        flash("Post not found.")

    return redirect(url_for("dashboard") + "#student-feed")


# --------------------------------------------------
# ADD COMMENT
# --------------------------------------------------

@app.route("/post/<int:post_id>/comment", methods=["POST"])
def add_comment(post_id):

    if not login_required():
        return redirect(url_for("login"))

    content = request.form.get("content", "").strip()

    if not content:
        flash("Comment cannot be empty.")

    elif len(content) > 500:
        flash("Comment cannot exceed 500 characters.")

    else:
        success = db.add_post_comment(
            post_id,
            session["user_id"],
            content
        )

        if not success:
            flash("Post not found.")

    return redirect(url_for("dashboard") + "#student-feed")


# --------------------------------------------------
# DELETE OWN COMMENT
# --------------------------------------------------

@app.route("/comment/<int:comment_id>/delete", methods=["POST"])
def delete_comment(comment_id):

    if not login_required():
        return redirect(url_for("login"))

    success = db.delete_post_comment(
        comment_id,
        session["user_id"]
    )

    if not success:
        flash("Comment not found or permission denied.")

    return redirect(url_for("dashboard") + "#student-feed")


@app.route("/student/<int:student_id>")
def view_student(student_id):

    if not login_required():
        return redirect(url_for("login"))

    student = db.get_user_by_id(student_id)
    student_profile = db.get_profile(student_id)

    if student is None or student_profile is None:
        flash("Student not found.", "error")
        return redirect(url_for("search"))

    refresh_network()

    current_user_id = session["user_id"]

    path = network.shortest_path(
        current_user_id,
        student_id
    )

    degree = len(path) - 1 if path else -1

    return render_template(
        "view_student.html",
        student=student,
        profile=student_profile,
        degree=degree
    )

# --------------------------------------------------
# 16. RUN THE APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)


