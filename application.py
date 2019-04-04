# this is project1 from HarvardX: CS50W
# CS50's Web Programming with Python and JavaScript
# https://courses.edx.org/courses/course-v1:HarvardX+CS50W+Web/course/#block-v1:HarvardX+CS50W+Web+type@sequential+block@c62f675bf7f94f0e91b408cacda56451

# short description : To create a webapp  where user can search for books ,read review from other user and also write review.
# some of the requirement of project is not completed 1. rating system
#  when i created column for isbn in my database i created it as integer which should had been string so my isbn database  might not be accurate

# DATABASE : psql
# FRAMEWORK: flask

from flask import Flask, session, request, render_template, url_for, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from goodreads import client
engine = create_engine(
    "postgres://jrcviumsdleoov:735447402e7a747663c9bea9a63516077b97b9fbcd3263c7b6f7e00f1fcced1b@ec2-54-221-243-211.compute-1.amazonaws.com:5432/dlstk1fcf3fjd")
     #PLEASE DON'T INSERT ANY DATA IN THIS DATABASE
db = scoped_session(sessionmaker(bind=engine))
app = Flask(__name__)
app.config['SESSION_PERMANENT'] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
def index():
    if session.get("login") is None:
        session["login"] = False
  
# if user is logged in will see search page
    if session['login']:
       return render_template("search_book.html", user=session['user'])
    
    return redirect(url_for("login_page"))
    
    


@app.route("/register_form")
def register_form():

    return render_template("registration_form.html")


@app.route('/signup_confirmation', methods=['POST', 'GET'])
def register():
    # check for http method (only post method is valid)
    if request.method == 'GET':
        return "go to registration page"
    if request.method == "POST":
        # get user inputs
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email_address")
        birth_day = request.form.get('birth_day')
        user_name = request.form.get("user_name")
        pwd = request.form.get("password")

        # check if user_name is available
        user_names = db.execute("SELECT user_name FROM members").fetchall()
        for name, in user_names:
            if name == user_name:
                return "<h1> ERROR: User Name taken <p> GO BACK try different user name</p></h1>"

        # register user if user_name is available
        # table named "members" is already created with column id , first_name, last_name, email, birthday
        db.execute("INSERT INTO members "
                   "(first_name, last_name, email, user_name, birthday)"
                   " VALUES(:first_name ,:last_name,:email,:user_name,:birth_day)",
                   {"first_name": first_name, "last_name": last_name, "email": email, "user_name": user_name,
                    "birth_day": birth_day})
        # password will be registered in different table called "pwds"
        # pwds has two column id and password ( id column of members and pwds will be same )

        db.execute("INSERT INTO pwds (password) VALUES(:pwd)", {"pwd": pwd})
        db.commit()
        return render_template("registered.html", name=first_name)


@app.route("/login_page", methods=["GET"])
def login_page():
    if session["login"] == False:
       return render_template("login.html")
    else:
        return "already logged in"


@app.route("/login_confirmation", methods=['POST'])
def login():
    # get user name and password
    user_name = request.form.get("user_name")
    password = request.form.get("password")

    # check if user exist
    if db.execute("SELECT user_name FROM members WHERE user_name=:user_name",{"user_name":user_name}).fetchone() is None:
       return "ERROR: user does not exist"

    # check if passoword is correct
    id, user = db.execute("SELECT id,user_name FROM members WHERE user_name =:user_name",
                          {"user_name": user_name}).fetchone()
    pwd, = db.execute("SELECT password FROM pwds WHERE id=:id",
                      {'id': id}).fetchone()
    if pwd == password:
        session["login"] = True
        session["user"] = user_name
        return redirect(url_for('index'))
    else:
        return " password incorrect"


@app.route("/logout")
def logout():

    if session['login']:
        session['login'] = False
    return redirect(url_for("index"))



# search page
@app.route("/search_books",)
def search_page():
    # user can only access search page if logged in
    if session["login"]:
       return render_template("search_book.html", user=session['user'])
    return render_template("not_logged_in.html")


@app.route("/search_results", methods=['POST'])
def search_result():
    # get the keyword for search
    keyword = request.form.get("keyword")
    keyword = '%' + keyword + '%'

    # search for book that keyword match with either the title or author of book
    # table named books is already created with column isbn, title ,author and  pub_year
    book = db.execute("SELECT isbn ,title ,author FROM books WHERE title ILIKE :keyword OR author ILIKE :keyword;",{'keyword': keyword}).fetchall()
    return render_template("search_results.html", book=book, user=session['user'])


# user can also directly access this page by url by passing isbn of the book if logged in
@app.route("/details/<int:isbn>")
def detail(isbn):
    if session['login'] == False or session['login'] == None:
        return render_template("not_logged_in.html")

    book_isbn = isbn
    book = db.execute("SELECT * FROM books WHERE isbn =:isbn ;", {'isbn':book_isbn}).fetchone();
    print(book)
    isbn, author, pub_year, title = book
    reviews = db.execute("SELECT * FROM reviews WHERE isbn=:isbn;",{'isbn':isbn}).fetchall()
    return render_template("details.html", isbn=isbn, author=author, pub_year=pub_year, title=title,reviews=reviews,user=session['user'])
    


@app.route("/write_review/<int:isbn>")
def write_review(isbn):
    if session['login'] == False or session['login'] == None:
        return render_template("not_logged_in.html")
    reviewers = db.execute("SELECT reviewer FROM reviews WHERE isbn=:isbn;",{"isbn": isbn}).fetchall()
    for user, in reviewers:
        if user == session['user']:
            return "can only review one time"
        
    return render_template("write_review.html",isbn=isbn)


@app.route("/post_review/<isbn>",methods=['POST'])
def post_review(isbn):
    review = request.form.get('review')
    reviewer = session['user']
    isbn = isbn

    db.execute("INSERT INTO reviews (isbn, reviewer,review)"
               "VALUES(:isbn,:reviewer,:review);",{'isbn':isbn, 'reviewer':reviewer, "review":review})
    db.commit()
    return "your review is posted"


# api from goodreads
@app.route("/api/<string:isbn>")
def goodreads(isbn):
    cl = client.GoodreadsClient("YwoRrbmvD1xQgyfIIOPQ", "INo8jC4JeAVOiXFckzQPKqYYeuq2wFLJyBKQmidDy0")
    book = cl.book(isbn=isbn)
    title = book.title
    authors = book.authors
    author = ''
    for a in authors:
        author += a.__repr__()
        author += ", "
    avg_rating = book.average_rating
    rev_count = book.text_reviews_count
    
    return jsonify({
        "title": title
        "author": author
        "avg_rating": avg_rating
        "rev_count": rev_count
    })   
    



if __name__ == "__main__":
    app.run(debug=True)
