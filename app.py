import os
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

@app.route("/")
@app.route("/get_rooms")
def get_rooms():
    rooms = list(mongo.db.rooms.find())
    return render_template("rooms.html", rooms=rooms)


@app.route("/get_tasks")
def get_tasks():
    tasks = list(mongo.db.tasks.find())
    return render_template("tasks.html", tasks=tasks)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # checks if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exist in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # check hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(
                        request.form.get("username")))
                    return redirect(url_for(
                        "profile", username=session["user"]))  
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # get the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    #remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        is_urgent = "on" if request.form.get("is_urgent") else "off"
        task = {
            "employee_name": request.form.get("employee_name"),
            "room_type": request.form.get("room_type"),
            "room_number": request.form.get("room_number"),
            "due_date": request.form.get("due_date"),
            "is_urgent": is_urgent,
            "created_by": session["user"]
        }
        mongo.db.tasks.insert_one(task)
        flash("Task Successfully Added")
        return redirect(url_for("get_tasks"))
        
    categories = mongo.db.categories.find().sort("room_type", 1)
    rooms = mongo.db.rooms.find().sort("room_number", 1)
    housekeepers = mongo.db.housekeepers.find().sort("employee_name", 1)

    return render_template("add_task.html", categories=categories,
         rooms=rooms, housekeepers=housekeepers)


@app.route("/edit_task/<task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})

    categories = mongo.db.categories.find().sort("room_type", 1)
    rooms = mongo.db.rooms.find().sort("room_number", 1)
    housekeepers = mongo.db.housekeepers.find().sort("employee_name", 1)

    return render_template("edit_task.html", task=task, categories=categories,
         rooms=rooms, housekeepers=housekeepers)



if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
    port=int(os.environ.get("PORT")),
    debug=True)
