from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from datetime import timedelta, datetime
import jwt
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor


app = Flask(__name__)
CORS(
    app,
    supports_credentials=True,
    resources={
        r"/*": {
            "origins": ["https://library-klmc.onrender.com/", "http://127.0.0.1:9000/"]
        }
    },
)
load_dotenv()
app.secret_key = os.getenv("secret_key")


# development: http://127.0.0.1:9000/
# production: https://library-klmc.onrender.com/
def get_connection():
    conn = psycopg2.connect(
        host=os.getenv("db_host"),
        database=os.getenv("db_name"),
        user=os.getenv("db_user"),
        password=os.getenv("db_password"),
        port=os.getenv("db_port"),
    )
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS books(id SERIAL PRIMARY KEY ,ISBN VARCHAR(20) UNIQUE ,name VARCHAR(150) NOT NULL,author VARCHAR(100) NOT NULL,quantity INT NOT NULL CHECK (quantity >= 0),img TEXT NOT NULL)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS readers(id SERIAL PRIMARY KEY ,name VARCHAR(50) NOT NULL,email VARCHAR(100) UNIQUE NOT NULL,password VARCHAR(100) NOT NULL,phone VARCHAR(20) UNIQUE)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS rented(id SERIAL PRIMARY KEY ,bookId INT NOT NULL,readerId INT NOT NULL,rentDate DATE,returnDate DATE,FOREIGN KEY(bookId) REFERENCES books(id) ON DELETE CASCADE,FOREIGN KEY(readerId) REFERENCES readers(id) ON DELETE CASCADE) "
    )
    conn.commit()
    conn.close()


# SESSION CONTROL


@app.route("/", methods=["POST", "GET"])
def login():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    if request.method == "POST":
        user_data = request.json
        cursor.execute(
            "SELECT * FROM readers WHERE email=%s AND password=%s",
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
            return jsonify(
                {"response": "success", "message": "Logged In", "token": token}
            )
        else:
            return jsonify({"response": "failed", "reader": "no user exists"})
    cursor.execute("SELECT * FROM readers")
    rows = cursor.fetchall()
    users = [dict(row) for row in rows]
    return users


def decode_jwt(token):
    payload = jwt.decode(token, app.secret_key, algorithms=["HS256"])
    if payload:
        return payload
    else:
        return False


@app.route("/get_session/")
def get_session():
    auth_header = request.headers.get("Authorization")
    if auth_header:
        token = auth_header.split(" ")[1]
        payload = decode_jwt(token)
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
    resp.set_cookie(
        "jwt_token", "", httponly=True, expires=0, secure=True, samesite="Strict"
    )
    return resp


# GET BOOKS IS GENERAL


@app.route("/books/", methods=["GET"])
def get_books():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute(
        "SELECT books.id,books.ISBN,books.name,books.author,books.img,books.quantity-COALESCE(COUNT(rented.id),0) AS available_quantity , books.quantity AS total_quantity FROM books LEFT JOIN rented ON books.id = rented.bookId GROUP BY books.id"
    )
    rows = cursor.fetchall()
    books = [dict(row) for row in rows]
    return jsonify(books)


# BOOK OPERATIONS ARE ADMIN


@app.route("/books/", methods=["POST"])
def add_book():
    conn = get_connection()
    cursor = conn.cursor()
    data = request.json
    cursor.execute(
        "INSERT INTO books(name,author,img,isbn,quantity) VALUES(%s,%s,%s,%s,%s)",
        (
            data.get("name"),
            data.get("author"),
            data.get("img"),
            data.get("isbn"),
            data.get("quantity"),
        ),
    )
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return jsonify({"response": "success", "message": "Book Added Succesfully"})
    else:
        return jsonify({"response": "failed", "message": "Error Occured"})


@app.route("/books/<int:id>/", methods=["DELETE"])
def delete_book(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return jsonify({"response": "success", "message": "Book Deleted Succesfully"})


@app.route("/books/<int:id>/", methods=["PUT"])
def edit_book(id):
    conn = get_connection()
    cursor = conn.cursor()
    data = request.json
    print(data)
    columns = ", ".join([f"{key} =%s" for key in data.keys()])
    values = list(data.values())
    values.append(id)
    query = f"UPDATE books SET {columns} WHERE id = %s"
    cursor.execute(query, tuple(values))
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return jsonify({"response": "success", "message": "Book Updated Succesfully"})
    else:
        return jsonify({"response": "failed", "message": "Error Occured"})


# GET RENTED GENERAL


@app.route("/books_rented/", methods=["GET", "POST"])
def get_rented():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    if request.method == "GET":
        cursor.execute("SELECT * FROM rented")
        rows = cursor.fetchall()
        rented = [dict(row) for row in rows]
        return jsonify(rented)
    elif request.method == "POST":
        user = request.json
        user_id = user["userId"]
        cursor.execute("SELECT * FROM rented WHERE readerId=%s", (user_id,))
        rows = cursor.fetchall()
        rented = [dict(row) for row in rows]
        return jsonify(rented)


# GET READERS IS ADMIN


@app.route("/readers/", methods=["GET"])
def get_readers():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM readers WHERE id != 1")
    rows = cursor.fetchall()
    readers = [dict(row) for row in rows]
    return jsonify(readers)


# RENT AND RETURN ARE USER


@app.route("/rent_book/<int:id>/")
def rent_book(id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM books WHERE id=%s", (id,))
    row = cursor.fetchone()
    book = dict(row)
    auth_header = request.headers.get("Authorization")
    if auth_header:
        token = auth_header.split(" ")[1]
        payload = decode_jwt(token)
        reader = payload.get("user_id")
        cursor.execute(
            "SELECT * FROM rented WHERE bookId=%s AND readerId=%s",
            (book.get("id"), reader),
        )
        row = cursor.fetchone()
        if row:
            return jsonify(
                {"response": "failed", "message": "You have already Rented this book"}
            )
        cursor.execute(
            "SELECT COUNT(*) FROM rented WHERE readerId=%s",
            (reader,),
        )
        rent_limit = cursor.fetchone()[0] + 1

        if rent_limit > 3:
            return jsonify(
                {"response": "failed", "message": "You have already Rented Three Books"}
            )
        cursor.execute(
            "INSERT INTO rented(bookId,readerId,rentDate,returnDate) VALUES (%s,%s,NOW(),NOW() + INTERVAL '10 days')",
            (book.get("id"), reader),
        )
        conn.commit()
        conn.close()
        return jsonify({"response": "success", "message": "Book Rented Succesfully"})
    return jsonify({"response": "fail", "message": "Failure"})


@app.route("/return_book/<int:id>/")
def return_book(id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM books WHERE id=%s", (id,))
    row = cursor.fetchone()
    book = dict(row)
    auth_header = request.headers.get("Authorization")
    if auth_header:
        token = auth_header.split(" ")[1]
        payload = decode_jwt(token)
        reader = payload.get("user_id")
        cursor.execute(
            "DELETE FROM rented WHERE bookId=%s AND readerId=%s",
            (book.get("id"), reader),
        )
        conn.commit()
        conn.close()
        return jsonify({"response": "success", "message": "Book Returned Succesfully"})


if __name__ == "__main__":
    create_tables()
    app.run(debug=True, port=9000)
