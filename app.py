from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import sqlite3
from datetime import timedelta, datetime
import jwt


app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = "secret_key"


# development: http://127.0.0.1:9000/
# production: https://library-klmc.onrender.com/
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
            user = dict(row)
            payload = {
                "user_id": user.get("id"),
                "user_name": user.get("name"),
                "exp": datetime.now() + timedelta(minutes=30),
            }
            token = jwt.encode(payload, app.secret_key, algorithm="HS256")
            resp = make_response(
                jsonify({"response": "success", "message": "Logged In"})
            )
            resp.set_cookie("jwt_token", token, httponly=True, secure=True)
            return resp
        else:
            return jsonify({"response": "failed", "reader": "no user exists"})
    cursor.execute("SELECT * FROM readers")
    rows = cursor.fetchall()
    users = [dict(row) for row in rows]
    return users


def decode_jwt():
    token = request.cookies.get("jwt_token")
    if token:
        payload = jwt.decode(token, app.secret_key, algorithms=["HS256"])
        return payload
    else:
        return False


@app.route("/get_session/")
def get_session():
    payload = decode_jwt()
    if payload:
        user_id = payload.get("user_id")
        user_name = payload.get("user_name")
        return jsonify(
            {"userId": user_id, "userName": user_name, "message": "Token found"}
        )
    else:
        return jsonify({"message": "Token not found"})


@app.route("/logout/")
def logout():
    resp = make_response(jsonify({"response": "logged out"}))
    resp.set_cookie("jwt_token", "", expires=0, httponly=True, secure=True)
    return resp


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
    payload = decode_jwt()
    reader = payload.get("user_id")
    cursor.execute(
        "SELECT * FROM rented WHERE bookId=? AND readerId=?",
        (book.get("id"), reader),
    )
    row = cursor.fetchone()
    if row:
        return jsonify(
            {"response": "failed", "message": "You have already Rented this book"}
        )
    cursor.execute(
        "SELECT COUNT(*) FROM rented WHERE readerId=?",
        (reader,),
    )
    rent_limit = cursor.fetchone()[0] + 1

    if rent_limit > 3:
        return jsonify(
            {"response": "failed", "message": "You have already Rented Three Books"}
        )
    cursor.execute(
        "INSERT INTO rented(bookId,readerId,rentDate,returnDate) VALUES (?,?,datetime('now','localtime'),datetime('now','+10 days','localtime'))",
        (book.get("id"), reader),
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
    payload = decode_jwt()
    reader = payload.get('user_id')
    cursor.execute(
        "DELETE FROM rented WHERE bookId=? AND readerId=?",
        (book.get("id"), reader),
    )
    conn.commit()
    conn.close()
    return jsonify({"response": "success", "message": "Book Returned Succesfully"})


if __name__ == "__main__":
    create_tables()
    app.run(debug=True, port=9000)
