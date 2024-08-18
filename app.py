from flask import Flask, request, jsonify, session, make_response

# from flask_session import Session
from flask_cors import CORS
import sqlite3
from datetime import timedelta, datetime

# import redis

app = Flask(__name__)
CORS(app, supports_credentials=True)
# , origins=["https://petervol27.github.io"]
app.secret_key = "secret key"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
app.config.update(
    SESSION_COOKIE_SECURE=True,  # Use True if your site uses HTTPS
    SESSION_COOKIE_SAMESITE="Lax",  # Adjust as needed
    SESSION_COOKIE_HTTPONLY=True,  # Recommended for security
    SESSION_COOKIE_DOMAIN=".library-klmc.onrender.com",  # Update based on your domain
)
# app.config["SESSION_TYPE"] = "redis"
# app.config["SESSION_TYPE"] = "filesystem"
# app.config["SESSION_REDIS"] = redis.from_url("redis://red-cr0e93rv2p9s73a6jd50:6379")
# app.config["SESSION_REDIS"] = redis.from_url("redis://localhost:6379/0")
# Session(app)
# app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# app.config["SESSION_COOKIE_SERCURE"] = True
# app.config["SESSION_COOKIE_DOMAIN"] = "https://library-klmc.onrender.com"
# app.config["SESSION_COOKIE_PATH"] = "/"
# app.config.update(
#     SESSION_COOKIE_SECURE=True,
#     SESSION_COOKIE_SAMESITE="Lax",
# )
# app.config["SESSION_COOKIE_DOMAIN"] = ".https://library-klmc.onrender.com/"
# dev_env = "http://127.0.0.1:9000"
# prod_env = "https://library-klmc.onrender.com/"
# Session(app)


def get_connection():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS books(id INTEGER PRIMARY KEY  AUTOINCREMENT,ISBN TEXT NOT NULL,name TEXT NOT NULL,author TEXT NOT NULL,quantity INTEGER,img TEXT NOT NULL)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS readers(id INTEGER PRIMARY KEY  AUTOINCREMENT,name TEXT NOT NULL,email TEXT NOT NULL,password TEXT NOT NULL,phone TEXT UNIQUE)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS rented(id INTEGER  PRIMARY KEY AUTOINCREMENT,bookId,readerId,rentDate TEXT,returnDate TEXT,FOREIGN KEY(bookId) REFERENCES books(id),FOREIGN KEY(readerId) REFERENCES readers(id)) "
    )


def set_session(obj):
    session["reader"] = obj


@app.route("/", methods=["POST", "GET"])
def login():
    conn = get_connection()
    cursor = conn.cursor()
    if request.method == "POST":
        user_data = request.json
        cursor.execute(
            "SELECT * FROM readers WHERE email=? AND password=?",
            (user_data["email"], user_data["password"]),
        )
        row = cursor.fetchone()
        if row:
            set_session(dict(row))
            return jsonify({"response": "success", "reader": dict(row)})
        else:
            return jsonify({"response": "failed", "reader": "no user exists"})
    cursor.execute("SELECT * FROM readers")
    rows = cursor.fetchall()
    users = [dict(row) for row in rows]
    return users


@app.route("/get_session/")
def get_session():
    reader = session.get("reader")
    if reader:
        print("reader:" + reader)
        return jsonify(reader=reader)
    else:
        print("no session set")
        return jsonify({"response": "no session set"})


@app.route("/set_test_session")
def set_test_session():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM readers WHERE id=1",
    )
    row = cursor.fetchone()
    if row:
        session["test"] = dict(row)
        return jsonify({"response": "Session set"})


@app.route("/get_test_session")
def get_test_session():
    test_value = session.get("test", "No session found")
    print("Session value:", test_value)  # Check the server logs for this output
    return jsonify({"session_value": test_value})


@app.route("/logout/")
def logout():
    session.pop("reader", None)
    return jsonify({"response": "logged out"})


@app.route("/books/", methods=["GET"])
def get_books():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT books.id,books.ISBN,books.name,books.author,books.img,books.quantity-COALESCE(COUNT(rented.id),0) AS available_quantity , books.quantity AS total_quantity FROM books LEFT JOIN rented ON books.id = rented.bookId GROUP BY books.id"
    )
    rows = cursor.fetchall()
    books = [dict(row) for row in rows]
    return jsonify(books)


@app.route("/books_rented/", methods=["GET", "POST"])
def get_rented():
    conn = get_connection()
    cursor = conn.cursor()
    if request.method == "GET":
        cursor.execute("SELECT * FROM rented")
        rows = cursor.fetchall()
        rented = [dict(row) for row in rows]
        return jsonify(rented)
    elif request.method == "POST":
        user = request.json
        user_id = user["userId"]
        cursor.execute("SELECT * FROM rented WHERE readerId=?", (user_id,))
        rows = cursor.fetchall()
        rented = [dict(row) for row in rows]
        return jsonify(rented)


@app.route("/readers/", methods=["GET"])
def get_readers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM readers WHERE ID != 1")
    rows = cursor.fetchall()
    readers = [dict(row) for row in rows]
    return jsonify(readers)


@app.route("/rent_book/<int:id>/")
def rent_book(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id=?", (id,))
    row = cursor.fetchone()
    book = dict(row)
    reader = session.get("reader")
    cursor.execute(
        "SELECT * FROM rented WHERE bookId=? AND readerId=?",
        (book.get("id"), reader.get("id")),
    )
    row = cursor.fetchone()
    if row:
        return jsonify(
            {"response": "failed", "message": "You have already Rented this book"}
        )
    cursor.execute(
        "SELECT COUNT(*) FROM rented WHERE readerId=?",
        (reader.get("id"),),
    )
    rent_limit = cursor.fetchone()[0] + 1

    if rent_limit > 3:
        return jsonify(
            {"response": "failed", "message": "You have already Rented Three Books"}
        )
    cursor.execute(
        "INSERT INTO rented(bookId,readerId,rentDate,returnDate) VALUES (?,?,datetime('now','localtime'),datetime('now','+10 days','localtime'))",
        (book.get("id"), reader.get("id")),
    )
    conn.commit()
    conn.close()
    return jsonify({"response": "success", "message": "Book Rented Succesfully"})


@app.route("/return_book/<int:id>/")
def return_book(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id=?", (id,))
    row = cursor.fetchone()
    book = dict(row)
    reader = session.get("reader")
    cursor.execute(
        "DELETE FROM rented WHERE bookId=? AND readerId=?",
        (book.get("id"), reader.get("id")),
    )
    conn.commit()
    conn.close()
    return jsonify({"response": "success", "message": "Book Returned Succesfully"})


if __name__ == "__main__":
    create_tables()
    app.run(debug=True, port=9000)
