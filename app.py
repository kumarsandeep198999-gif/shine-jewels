from flask import Flask, render_template, request, redirect, url_for, session
import os
import sqlite3
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "shine-jewels-secret-key"


# =========================
# DATABASE
# =========================

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():

    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)

    return sqlite3.connect("shine_jewels.db")


def create_database():

    conn = get_db()

    if DATABASE_URL:

        # =========================
        # POSTGRESQL - RENDER
        # =========================

        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price TEXT NOT NULL,
                quantity INTEGER DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wishlist (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price TEXT NOT NULL
            )
        """)

        conn.commit()
        cursor.close()

    else:

        # =========================
        # SQLITE - LOCAL COMPUTER
        # =========================

        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price TEXT NOT NULL,
                quantity INTEGER DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wishlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price TEXT NOT NULL
            )
        """)

        conn.commit()
        cursor.close()

    conn.close()


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        try:

            conn = get_db()
            cursor = conn.cursor()

            if DATABASE_URL:

                cursor.execute(
                    """
                    INSERT INTO users (name, email, password)
                    VALUES (%s, %s, %s)
                    """,
                    (name, email, hashed_password)
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO users (name, email, password)
                    VALUES (?, ?, ?)
                    """,
                    (name, email, hashed_password)
                )

            conn.commit()

            cursor.close()
            conn.close()

            return redirect(url_for("login"))

        except Exception as e:

            try:
                conn.rollback()
                conn.close()
            except:
                pass

            if "unique" in str(e).lower() or "duplicate" in str(e).lower():

                return "Email already registered. Please use another email."

            return f"Database error: {e}"

    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        if DATABASE_URL:

            cursor.execute(
                """
                SELECT * FROM users
                WHERE email = %s
                """,
                (email,)
            )

        else:

            cursor.execute(
                """
                SELECT * FROM users
                WHERE email = ?
                """,
                (email,)
            )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(
            user[3],
            password
        ):

            session["user_id"] = user[0]
            session["user_name"] = user[1]

            return redirect(url_for("home"))

        return "Invalid email or password."

    return render_template("login.html")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =========================
# ADD TO CART
# =========================

@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():

    if "user_id" not in session:
        return redirect(url_for("login"))

    product_name = request.form["product_name"]
    price = request.form["price"]

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    # Check if product already exists

    if DATABASE_URL:

        cursor.execute(
            """
            SELECT id, quantity
            FROM cart
            WHERE user_id = %s
            AND product_name = %s
            """,
            (user_id, product_name)
        )

    else:

        cursor.execute(
            """
            SELECT id, quantity
            FROM cart
            WHERE user_id = ?
            AND product_name = ?
            """,
            (user_id, product_name)
        )

    existing = cursor.fetchone()

    if existing:

        # Increase quantity

        if DATABASE_URL:

            cursor.execute(
                """
                UPDATE cart
                SET quantity = quantity + 1
                WHERE id = %s
                """,
                (existing[0],)
            )

        else:

            cursor.execute(
                """
                UPDATE cart
                SET quantity = quantity + 1
                WHERE id = ?
                """,
                (existing[0],)
            )

    else:

        # Add new product

        if DATABASE_URL:

            cursor.execute(
                """
                INSERT INTO cart
                (user_id, product_name, price, quantity)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, product_name, price, 1)
            )

        else:

            cursor.execute(
                """
                INSERT INTO cart
                (user_id, product_name, price, quantity)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, product_name, price, 1)
            )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("cart"))


# =========================
# CART
# =========================

@app.route("/cart")
def cart():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    if DATABASE_URL:

        cursor.execute(
            """
            SELECT id, product_name, price, quantity
            FROM cart
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

    else:

        cursor.execute(
            """
            SELECT id, product_name, price, quantity
            FROM cart
            WHERE user_id = ?
            """,
            (session["user_id"],)
        )

    items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "cart.html",
        items=items
    )


# =========================
# WISHLIST
# =========================

@app.route("/wishlist")
def wishlist():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    if DATABASE_URL:

        cursor.execute(
            """
            SELECT id, product_name, price
            FROM wishlist
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

    else:

        cursor.execute(
            """
            SELECT id, product_name, price
            FROM wishlist
            WHERE user_id = ?
            """,
            (session["user_id"],)
        )

    items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "wishlist.html",
        items=items
    )


# =========================
# ADD TO WISHLIST
# =========================

@app.route("/add-to-wishlist", methods=["POST"])
def add_to_wishlist():

    if "user_id" not in session:
        return redirect(url_for("login"))

    product_name = request.form["product_name"]
    price = request.form["price"]

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    # Check if product already exists

    if DATABASE_URL:

        cursor.execute(
            """
            SELECT id
            FROM wishlist
            WHERE user_id = %s
            AND product_name = %s
            """,
            (user_id, product_name)
        )

    else:

        cursor.execute(
            """
            SELECT id
            FROM wishlist
            WHERE user_id = ?
            AND product_name = ?
            """,
            (user_id, product_name)
        )

    existing = cursor.fetchone()

    # Add only if not already in wishlist

    if not existing:

        if DATABASE_URL:

            cursor.execute(
                """
                INSERT INTO wishlist
                (user_id, product_name, price)
                VALUES (%s, %s, %s)
                """,
                (user_id, product_name, price)
            )

        else:

            cursor.execute(
                """
                INSERT INTO wishlist
                (user_id, product_name, price)
                VALUES (?, ?, ?)
                """,
                (user_id, product_name, price)
            )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("wishlist"))


# =========================
# JEWELLERY PAGES
# =========================

@app.route("/gold")
def gold():
    return render_template("gold.html")


@app.route("/diamond")
def diamond():
    return render_template("diamond.html")


@app.route("/earrings")
def earrings():
    return render_template("earrings.html")


@app.route("/dailywear")
def dailywear():
    return render_template("dailywear.html")


@app.route("/gemstone")
def gemstone():
    return render_template("gemstone.html")


@app.route("/wedding")
def wedding():
    return render_template("wedding.html")


@app.route("/gifting")
def gifting():
    return render_template("gifting.html")


@app.route("/under50k")
def under50k():
    return render_template("under50k.html")


@app.route("/price50to1lakh")
def price50to1lakh():
    return render_template("price50to1lakh.html")


@app.route("/premium")
def premium():
    return render_template("premium.html")


@app.route("/newarrivals")
def newarrivals():
    return render_template("newarrivals.html")


@app.route("/bestsellers")
def bestsellers():
    return render_template("bestsellers.html")


@app.route("/offers")
def offers():
    return render_template("offers.html")


# =========================
# PRODUCT PAGE
# =========================

@app.route("/product/<product_name>")
def product(product_name):

    products = {

        "gold-ring": {
            "name": "Elegant Gold Ring",
            "price": "24,999",
            "icon": "💍",
            "description": "Beautiful gold ring for everyday style."
        },

        "diamond-earrings": {
            "name": "Diamond Earrings",
            "price": "39,999",
            "icon": "👂",
            "description": "Elegant diamond earrings for women."
        },

        "gold-necklace": {
            "name": "Gold Necklace",
            "price": "45,999",
            "icon": "📿",
            "description": "Classic gold necklace for special occasions."
        },

        "gemstone-ring": {
            "name": "Gemstone Ring",
            "price": "18,999",
            "icon": "💎",
            "description": "Beautiful gemstone ring with premium design."
        }

    }

    product = products.get(product_name)

    if product is None:
        return "Product Not Found", 404

    return render_template(
        "product.html",
        product=product
    )


# =========================
# START SERVER
# =========================

try:
    create_database()
except Exception as e:
    print("Database initialization error:", e)


if __name__ == "__main__":
    app.run(debug=True)