import psycopg2

books = [
    {
        "name": "To Kill a Mockingbird",
        "author": "Harper Lee",
        "quantity": 3,
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/To_Kill_a_Mockingbird_%28first_edition_cover%29.jpg/1200px-To_Kill_a_Mockingbird_%28first_edition_cover%29.jpg",
        "isbn": "978-0061120084",
    },
    {
        "name": "1984",
        "author": "George Orwell",
        "quantity": 4,
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Nineteen_Eighty-Four_cover_Soviet_1984.jpg/220px-Nineteen_Eighty-Four_cover_Soviet_1984.jpg",
        "isbn": "9780451524935",
    },
    {
        "name": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "quantity": 8,
        "img": "https://upload.wikimedia.org/wikipedia/commons/7/7a/The_Great_Gatsby_Cover_1925_Retouched.jpg",
        "isbn": "9780743273565",
    },
    {
        "name": "Moby Dick",
        "author": "Herman Melville",
        "quantity": 5,
        "img": "https://upload.wikimedia.org/wikipedia/commons/3/36/Moby-Dick_FE_title_page.jpg",
        "isbn": "9781503280786",
    },
    {
        "name": "War and Peace",
        "author": "Leo Tolstoy",
        "quantity": 2,
        "img": "https://upload.wikimedia.org/wikipedia/commons/0/05/WarAndPeace.jpg",
        "isbn": "9781400079988",
    },
    {
        "name": "Pride and Prejudice",
        "author": "Jane Austen",
        "quantity": 3,
        "img": "https://upload.wikimedia.org/wikipedia/en/thumb/0/09/Brock_Pride_and_Prejudice.jpg/220px-Brock_Pride_and_Prejudice.jpg",
        "isbn": "9781503290563",
    },
    {
        "name": "The Catcher in the Rye",
        "author": "J.D. Salinger",
        "quantity": 1,
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/The_Catcher_in_the_Rye_%281951%2C_first_edition_cover%29.jpg/800px-The_Catcher_in_the_Rye_%281951%2C_first_edition_cover%29.jpg",
        "isbn": "9780316769488",
    },
]


readers = [
    {
        "name": "admin",
        "email": "admin@admin.com",
        "password": "admin",
        "phone": "0123456789",
    },
    {
        "name": "Lance",
        "email": "lance@mail.com",
        "password": "lance",
        "phone": "0534567164",
    },
    {
        "name": "Victor",
        "email": "victor@mail.com",
        "password": "victor",
        "phone": "0521474561",
    },
    {
        "name": "Bob",
        "email": "bob@mail.com",
        "password": "bob",
        "phone": "0551237852",
    },
    {
        "name": "Alex",
        "email": "alex@mail.com",
        "password": "alex",
        "phone": "0511114752",
    },
]

DATABASE_URL = "postgresql://pietro:cTEXJEBndJUKDLNchfSLjwqSR4jpCyBV@dpg-cr2dg1lsvqrc73fkkjdg-a.frankfurt-postgres.render.com/data_lm59"
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()
for book in books:
    cursor.execute(
        "INSERT INTO books(name,author,quantity,img,isbn) VALUES(%s,%s,%s,%s,%s)",
        (book["name"], book["author"], book["quantity"], book["img"], book["isbn"]),
    )
for reader in readers:
    cursor.execute(
        "INSERT INTO readers(name,email,password,phone) VALUES(%s,%s,%s,%s)",
        (
            reader["name"],
            reader["email"],
            reader["password"],
            reader["phone"],
        ),
    )
conn.commit()
conn.close()
