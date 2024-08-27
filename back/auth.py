from flask import Flask, Blueprint, request, jsonify, make_response
from connect import get_connection
from psycopg2.extras import DictCursor
from datetime import timedelta, datetime
import jwt
import os
from dotenv import load_dotenv

load_dotenv()
secret_key = os.getenv("secret_key")
auth_bp = Blueprint("auth", __name__)
conn = get_connection()
print(conn)


@auth_bp.route("/", methods=["POST", "GET"])
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
            token = jwt.encode(payload, secret_key, algorithm="HS256")
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
    payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    if payload:
        return payload
    else:
        return False


@auth_bp.route("/get_session/")
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


@auth_bp.route("/logout/")
def logout():
    resp = make_response(jsonify({"response": "logged out"}))
    resp.set_cookie(
        "jwt_token", "", httponly=True, expires=0, secure=True, samesite="Strict"
    )
    return resp
