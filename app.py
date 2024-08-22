from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from datetime import timedelta, datetime
import jwt
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor

app = Flask(__name__)
CORS(app, supports_credentials=True)
load_dotenv()
app.secret_key = os.getenv("secret_key")

DATABASE_URL = "postgresql://pietro:cTEXJEBndJUKDLNchfSLjwqSR4jpCyBV@dpg-cr2dg1lsvqrc73fkkjdg-a.frankfurt-postgres.render.com/data_lm59"


# development: http://127.0.0.1:9000/
# production: https://library-klmc.onrender.com/
# def get_connection():
#     conn = psycopg2.connect(
#         dbname="pietro-db",
#         user="pietro",
#         password="cTEXJEBndJUKDLNchfSLjwqSR4jpCyBV",
#         host="dpg-cr2dg1lsvqrc73fkkjdg-a.frankfurt-postgres.render.com",
#         port="5432",
#     )
#     return conn
def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
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


@app.route("/readers/", methods=["GET"])
def get_readers():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM readers WHERE id != 1")
    rows = cursor.fetchall()
    readers = [dict(row) for row in rows]
    return jsonify(readers)


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
