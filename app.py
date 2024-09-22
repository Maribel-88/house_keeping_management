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
    categories = list(mongo.db.categories.find())
    return render_template("get_rooms.html", categories=categories)

@app.route("/deluxe_rooms")
def deluxe_rooms():
    deluxe_rooms = list(mongo.db.deluxe_rooms.find())
    tasks = list(mongo.db.tasks.find())
    return render_template("deluxe_rooms.html", deluxe_rooms=deluxe_rooms,
        tasks=tasks)


@app.route("/deluxestudio_rooms")
def deluxestudio_rooms():
    deluxestudio_rooms = list(mongo.db.deluxestudio_rooms.find())
    tasks = list(mongo.db.tasks.find())
    return render_template("deluxestudio_rooms.html", 
        deluxestudio_rooms=deluxestudio_rooms, tasks=tasks)


@app.route("/premierstudio_rooms")
def premierstudio_rooms():
    premierstudio_rooms = list(mongo.db.premierstudio_rooms.find())
    tasks = list(mongo.db.tasks.find())
    return render_template("premierstudio_rooms.html", 
        premierstudio_rooms=premierstudio_rooms, tasks=tasks)


@app.route("/get_tasks")
def get_tasks():
    tasks = list(mongo.db.tasks.find())
    return render_template("tasks.html", tasks=tasks)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    tasks = list(mongo.db.tasks.find({"$text": {"$search": query}}))
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
    user_id = request.form.get("user_id")
   
    housekeeper = {"$set":{
        "employee_name": request.form.get("employee_name"),
        "designation": request.form.get("designation"),
        
    }}

    mongo.db.housekeepers.update_one({"_id": ObjectId(user_id)}, housekeeper)
    users = mongo.db.users.find().sort("username", 1)
    housekeepers = mongo.db.housekeepers.find().sort("username", 1)


    if session["user"]:
        return render_template("profile.html", username=username,
            housekeepers=housekeepers, users=users)

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
            "room_status": request.form.get("room_status"),
            "created_by": session["user"]
        }
        
        mongo.db.tasks.insert_one(task)
       

        flash("Task Successfully Added")
        return redirect(url_for("get_tasks"))
        
    categories = mongo.db.categories.find().sort("room_type", 1)
    housekeepers = mongo.db.housekeepers.find().sort("employee_name", 1)
    deluxe_rooms = mongo.db.deluxe_rooms.find().sort("room_number")
    deluxestudio_rooms = mongo.db.deluxestudio_rooms.find().sort("room_number")
    premierstudio_rooms = mongo.db.premierstudio_rooms.find().sort("room_number")
    room_status = mongo.db.room_status.find().sort("room_status")
    rooms = mongo.db.rooms.find().sort("room_number", 1)
    
    return render_template("add_task.html", categories=categories,
        housekeepers=housekeepers, deluxe_rooms=deluxe_rooms,
        deluxestudio_rooms=deluxestudio_rooms,
        premierstudio_rooms=premierstudio_rooms,
        room_status=room_status, rooms=rooms )


@app.route("/edit_task/<task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    if request.method == "POST":
        is_urgent = "on" if request.form.get("is_urgent") else "off"
        edited_info = {"$set": {
            "employee_name": request.form.get("employee_name"),
            "room_type": request.form.get("room_type"),
            "room_number": request.form.get("room_number"),
            "due_date": request.form.get("due_date"),
            "is_urgent": is_urgent,
            "created_by": session["user"]
        }}
        mongo.db.tasks.update_one({"_id": ObjectId(task_id)}, edited_info)
        
        flash("Task Successfully Updated")
        
    task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})
    categories = mongo.db.categories.find().sort("room_type", 1)
    rooms = mongo.db.rooms.find().sort("room_number", 1)
    housekeepers = mongo.db.housekeepers.find().sort("employee_name", 1)
    deluxe_rooms = mongo.db.deluxe_rooms.find().sort("room_number")
    deluxestudio_rooms = mongo.db.deluxestudio_rooms.find().sort("room_number")
    room_status = mongo.db.room_status.find().sort("room_status")

    return render_template("edit_task.html", task=task, categories=categories,
         rooms=rooms, housekeepers=housekeepers,
         deluxe_rooms=deluxe_rooms, room_status=room_status,
         deluxestudio_rooms=deluxestudio_rooms)


@app.route("/delete_task/<task_id>")
def delete_task(task_id):
    mongo.db.tasks.delete_one({"_id": ObjectId(task_id)})
    mongo.db.rooms.delete_one({"_id": ObjectId(task_id)})
    flash("Task Successfully Deleted")
    return redirect(url_for("get_tasks"))


@app.route("/get_categories")
def get_categories():
    categories = list(mongo.db.categories.find().sort("room_type", 1))
    return render_template("categories.html", categories=categories)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category = {
            "room_type": request.form.get("room_type")
        }
        mongo.db.categories.insert_one(category)
        flash("New Category Added")
        return redirect(url_for("get_categories"))

    return render_template("add_category.html")


@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if request.method == "POST":
        submit = {"$set": {
            "room_type": request.form.get("room_type")
        }}
        mongo.db.categories.update_one({"_id": ObjectId(category_id)}, submit)
        flash("Category Successfully Updated")
        return redirect(url_for("get_categories"))

    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category)


@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    mongo.db.categories.delete_one({"_id": ObjectId(category_id)})
    flash("Task Successfully Deleted")
    return redirect(url_for("get_categories"))


@app.route("/add_housekeepers", methods=["GET", "POST"])
def add_housekeepers():
    if request.method == "POST":
        housekeeper = {
            "employee_name": request.form.get("employee_name"),
            "designation": request.form.get("designation")
        }
        mongo.db.housekeepers.insert_one(housekeeper)
        flash("New Housekeeper Added")
    

    return render_template("housekeepers.html" )


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
    port=int(os.environ.get("PORT")),
    debug=True)
