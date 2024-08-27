import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor

load_dotenv()


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
