from flask import Flask, session,request,render_template,redirect,flash,url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import os
from werkzeug.security import check_password_hash, generate_password_hash
import requests

app = Flask(__name__)
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database

# database engine object from SQLAlchemy that manages connections to the database
engine = create_engine(os.getenv("DATABASE_URL"))

# create a 'scoped session' that ensures different users' interactions with the
# database are kept separate
db = scoped_session(sessionmaker(bind=engine))
@app.route("/",methods=["GET","POST"])
def login():
	if session.get("user") is None:
		session["user"]=[]
	if request.method == "POST":
		name = request.form.get("name")
		password = request.form.get("password")
		if db.execute("SELECT name from login WHERE name=:n and password=:pass",{"n":name,"pass":password}).rowcount ==1:
			session["user"].append(name)
			return redirect('/home')	
		else:
			error_msg="No User Found"
			return render_template("error.html",error=error_msg)
	if request.method=="GET":
		if len(session["user"])==0:
			return render_template("login.html")
		else:
			return redirect('/home')	

@app.route("/register",methods=["GET","POST"])
def register():
	if len(session.get("user")) ==0:
		session["user"]=[]
	else:
		return redirect("/home") 	
	if request.method=="GET":
		print("IN GET OF REGISTER")
		return render_template("register.html")
	if request.method=="POST":
		name=request.form.get("name")
		password=request.form.get("password")
		if db.execute("SELECT name from login where name=:name",{"name":name}).rowcount>0:
			return render_template("error.html",error="user name taken")
		else:
			db.execute("INSERT INTO login(name,password) VALUES (:name,:password)",{"name":name,"password":password})
			db.commit()
			flash('Account created', 'info')
			session["user"].append(name)
			return redirect("/home")

@app.route("/logout",methods=["GET"])
def logout():
	session.clear()
	return redirect("/")			
@app.route("/home",methods=["GET","POST"])
def home():
	if request.method=="GET":
		books=db.execute("SELECT * from books LIMIT 21").fetchall()
		print(session.get("user"))	
		return render_template("home.html",user=session.get("user"),books=books)
	if request.method =="POST":
		name = request.form.get("book")
		print(name)
		book = db.execute("SELECT * from books where title LIKE (:name) LIMIT 21",{"name":"%"+name+"%"}).fetchall()
		# print(book)
		if len(book) ==0:
			return render_template("error.html",error="book not found")	
		print(session.get("user"))	
		return render_template("home.html",user=session.get("user"),books=book)
@app.route("/book/<string:isbn>",methods=["GET","POST"])
def book(isbn):
	if request.method =="GET":
		book = db.execute("SELECT * from books where isbn=(:isbn) ",{"isbn":isbn}).fetchone()
		if len(book) == 0:
			return render_template("error.html",error="book not found")
		else:
			review = db.execute("SELECT * from reviews where isbn=(:isbn)",{"isbn":isbn}).fetchall()
			res = requests.get("https://www.goodreads.com/book/review_counts.json",params={"key":"6jLcdYMNS3lg7oM3PUlVdg","isbns":[book.isbn]})		
			data = res.json()
			print(data['books'][0].get("reviews_count"))
			data_b=data['books'][0]
			# data=data['books'][0]
			# print(data.get("review_count"))
			if res.status_code == 404:
				return render_template("error.html",error="no data found")
			return render_template("book_info.html",book=book,data=data_b,user=session.get("user"),reviews=review)	
	if request.method == "POST":
		rev = request.form.get("review")
		user = session.get("user")[0]
		if len(rev) > 0:
			db.execute("INSERT INTO reviews(name,isbn,review) VALUES (:user,:isbn,:review)",{"user":user,"isbn":isbn,"review":rev})
			db.commit()
			# return "done"
			return redirect(url_for('book',isbn=isbn))
		else:
			return render_template("error.html",error="no review submitted")						