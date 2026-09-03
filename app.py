from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "shine-jewels-secret-key"


# =========================
# DATABASE
# =========================

def create_database():

    conn = sqlite3.connect("shine_jewels.db")

    # USERS TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # CART TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price TEXT NOT NULL,
            quantity INTEGER DEFAULT 1
        )
    """)

    # WISHLIST TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price TEXT NOT NULL
        )
    """)

    conn.commit()
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

            conn = sqlite3.connect(
                "shine_jewels.db",
                timeout=10
            )

            conn.execute(
                """
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, hashed_password)
            )

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            return "Email already registered. Please use another email."

        except sqlite3.OperationalError as e:

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

        conn = sqlite3.connect(
            "shine_jewels.db",
            timeout=10
        )

        user = conn.execute(
            """
            SELECT * FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

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

    conn = sqlite3.connect("shine_jewels.db")

    # Check if product already exists
    existing = conn.execute(
        """
        SELECT id, quantity
        FROM cart
        WHERE user_id = ?
        AND product_name = ?
        """,
        (user_id, product_name)
    ).fetchone()

    if existing:

        # Product already exists
        # Increase quantity
        conn.execute(
            """
            UPDATE cart
            SET quantity = quantity + 1
            WHERE id = ?
            """,
            (existing[0],)
        )

    else:

        # New product
        conn.execute(
            """
            INSERT INTO cart
            (user_id, product_name, price, quantity)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, product_name, price, 1)
        )

    conn.commit()
    conn.close()

    return redirect(url_for("cart"))


# =========================
# CART
# =========================

@app.route("/cart")
def cart():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("shine_jewels.db")

    items = conn.execute(
        """
        SELECT id, product_name, price, quantity
        FROM cart
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "cart.html",
        items=items
    )


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

if __name__ == "__main__":

    create_database()

    app.run(debug=True)