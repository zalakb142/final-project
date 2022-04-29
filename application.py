from asyncio.windows_events import NULL
from email import message
from inspect import isbuiltin
import os
from turtle import title
import requests

from flask import Flask, session, render_template, request, abort, jsonify, flash, json
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_DATABASE_URI"]=os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))



username=[]

@app.route("/")
def index():
    return render_template("homepage.html")

@app.route("/Basemap", methods=["GET","POST"])
def Basemap():   
    return render_template("basemap.html")

@app.route("/Air", methods=["GET","POST"])
def Air():   
    return render_template("Air.html")

@app.route("/heatmap", methods=["GET","POST"])
def heatmap():   
    return render_template("heatmap.html")

@app.route("/activity_plan", methods=["GET","POST"])
def activity_plan():   
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    session["username"]=[]
    #Get the user information
    name = request.form.get("name")
    pwd = request.form.get("pwd")
    #Make sure the username available
    if db.execute("SELECT * from users where username=:name", {"name": name}).rowcount>0:
        return render_template("error.html", message="Username already exists.")
    db.execute("INSERT INTO users(username, password) VALUES(:name, :pwd)", {"name":name, "pwd":pwd})
    db.commit()
    return render_template("success.html", message="You have registered successfully.")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="GET":
        return render_template("login.html")
    if request.method=="POST":
        #Get the username and password
        name = request.form.get("name")
        pwd = request.form.get("pwd")
        session["username"]=name
        if db.execute("SELECT * from users where username=:name and password=:pwd", {"name": name, "pwd":pwd}).rowcount==0:
            return render_template("error.html", message="Incorrect username or password. Please try Again!")
        activitylist=[]
        activitylist=db.execute("SELECT activities from users where username=:user", {"user":name}).fetchall()
        return render_template("activities.html", user=name, activitylist=activitylist)

@app.route("/activities/<user>", methods=["GET","POST"])
def activities(user):
    if user not in session["username"]:
        return render_template('index.html') 
    if request.method=="GET":
        activitylist=[]
        activitylist=db.execute("SELECT activities from users where username=:user", {"user":user}).fetchall()
        if activitylist[0][0] is None:
                return render_template("error.html", message="You have not subscribed yet!")
        return render_template("activities.html", user=user, activitylist=activitylist)      
    if request.method=="POST":    
        activitylist=[]
        activity = request.form.get("plan")
        activitylist=db.execute("SELECT activities from users where username=:user", {"user":user}).fetchall()
        if not (activity is None) and not (activitylist[0][0] is None):
            if "'"+activity+"'" in activitylist[0][0]:
                return render_template("error.html", message="Already subscribed!")   
        db.execute("Update users set activities=activities||'{':activity'}' where username=:user", {"activity":activity,"user":user})
        db.commit()
        updatedlist=db.execute("SELECT activities from users where username=:user", {"user":user}).fetchall()
        return render_template("activities.html", user=user, message="You have subscribed successfully!", activitylist=updatedlist)

@app.route("/unsub/<user>", methods=["GET","POST"])
def unsub(user):
    if user not in session["username"]:
        return render_template('index.html')
    if request.method=="GET":
        activitylist=[]
        activitylist=db.execute("SELECT activities from users where username=:user", {"user":user}).fetchall()
        if activitylist[0][0] is None:
                return render_template("error.html", message="You have not subscribed yet!")  
        return render_template("unsub.html", user=user, activitylist=activitylist)      
    if request.method=="POST":
        activitylist=[]
        activity = request.form.get("plan")
        activitylist=db.execute("SELECT activities from users where username=:user", {"user":user}).fetchall()
        print(activitylist[0][0])
        if (activitylist[0][0] is None) or not activitylist[0][0]:
            return render_template("error.html", message="You have not subscribed yet!")
        if not (activity is None) and not (activitylist[0][0] is None):
            if not ("'"+activity+"'" in activitylist[0][0]):
                return render_template("error.html", message="Already Unsubscribed!")   
        db.execute("Update users set activities=array_remove(activities,'':activity'') where username=:user", {"activity":activity,"user":user})
        db.commit()
        updatedlist=db.execute("SELECT activities from users where username=:user", {"user":user}).fetchall()
        return render_template("unsub.html", user=user, message="You have unsubscribed successfully!", activitylist=updatedlist)



