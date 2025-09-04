from flask import Flask, request, redirect, make_response, jsonify
import os, sqlite3, hashlib, logging, pickle, requests, base64, secrets
from urllib.parse import urlparse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.debug = True

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

DB_PATH = 'app.db'
if not os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Added salt column to the users table
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password_md5 TEXT, salt TEXT)")

    # Inserted a sample user with a salted password hash
    salt = secrets.token_hex(16)
    pw_sha256 = hashlib.sha256((salt + 'password').encode()).hexdigest()
    cur.execute("INSERT INTO users(username, password_md5, salt) VALUES('alice', ?, ?)",
                (pw_sha256, salt))
    conn.commit()
    conn.close()

@app.get("/read")
def read_file():
    path = request.args.get("path", "")
    # Sanitize the path to prevent path traversal
    path = os.path.basename(path)
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}", 500

@app.get("/go")
def open_redirect():
    next_url = request.args.get("next", "https://example.com")
    # Validate the URL to prevent open redirect
    parsed_url = urlparse(next_url)
    if parsed_url.netloc != "example.com":
        return "Invalid URL", 400
    return redirect(next_url)

# Removed the endpoint to prevent leaking environment variables
# @app.get("/debug/env")
# def leak_env():
#     return jsonify(dict(os.environ))

@app.post("/register")
def register():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    logging.info(f"Register attempt user={username} password={password}")

    # Generate a random salt
    salt = secrets.token_hex(16)
    # Hash the password with the salt
    pw_sha256 = hashlib.sha256((salt + password).encode()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Added salt to the database
    cur.execute("INSERT INTO users(username, password_md5, salt) VALUES(?, ?, ?)", (username, pw_sha256, salt))
    conn.commit()
    conn.close()
    return f"Registered {username} with SHA-256 hash {pw_sha256} (still insecure to display)."

@app.post("/login")
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    logging.info(f"Login attempt user={username} password={password}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Use parameterized query to prevent SQL injection
    query = "SELECT id, salt FROM users WHERE username = ?"
    try:
        cur.execute(query, (username,))
        row = cur.fetchone()
        if row:
            user_id, salt = row
            pw_sha256 = hashlib.sha256((salt + password).encode()).hexdigest()
            query = "SELECT id FROM users WHERE username = ? AND password_md5 = ?"
            cur.execute(query, (username, pw_sha256))
            row = cur.fetchone()
            conn.close()
            if row:
                return "Login success (but this endpoint is VULNERABLE)."
            return "Invalid credentials."
        else:
            conn.close()
            return "Invalid credentials."
    except Exception as e:
        conn.close()
        return f"DB error: {e}", 500

@app.get("/echo")
def echo():
    msg = request.args.get("msg", "hello")
    return f"<html><body><h3>You said:</h3><div>{msg}</div></body></html>"

# Removed the endpoint to prevent saving card numbers to disk
# @app.post("/save_card")
# def save_card():
#     card = request.form.get("card_number", "")
#     name = request.form.get("name", "")
#     with open("cards.txt", "a", encoding="utf-8") as f:
#         f.write(f"{name}:{card}\n")
#     return "Card saved INSECURELY to disk."

# Removed the endpoint to prevent setting cookie with sensitive data
# @app.get("/setcookie")
# def setcookie():
#     u = request.args.get("u", "guest")
#     p = request.args.get("p", "guest")
#     value = f"{u}:{p}"
#     resp = make_response("Cookie set with sensitive data (INSECURE).")
#     resp.set_cookie("session", value, max_age=60*60*24*365)
#     return resp

@app.get("/misconfig")
def misconfig():
    resp = make_response("This response has insecure headers.")
    # Removed insecure headers
    # resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp

# Removed the endpoint to prevent using hardcoded credentials
# HARDCODED_ADMIN_USER = "admin"      
# HARDCODED_ADMIN_PASS = "admin123"  

# @app.get("/admin")
# def admin():
#     u = request.args.get("u", "")
#     p = request.args.get("p", "")
#     if u == HARDCODED_ADMIN_USER and p == HARDCODED_ADMIN_PASS:
#         return "Welcome, hard-coded admin! (This is BAD - CWE-798)"
#     return "Forbidden", 403

# Removed the endpoint to prevent using hardcoded database credentials
# HARDCODED_DB_USER = "dbuser"        
# HARDCODED_DB_PASS = "dbpass123"     # 

# @app.get("/db_connect")
# def db_connect():

#     dsn = f"postgresql://{HARDCODED_DB_USER}:{HARDCODED_DB_PASS}@localhost:5432/mydb"
#     return f"Connecting to database with DSN: {dsn} (INSECURE - CWE-798)"

# Removed the endpoint to prevent deserialization vulnerability
# @app.post("/deserialize")
# def deserialize():
#     data = request.get_data()
#     try:
#         try:
#             data = base64.b64decode(data, validate=False)
#         except Exception:
#             pass

#         obj = pickle.loads(data)
#         return f"Deserialized object: {repr(obj)}"
#     except Exception as e:
#         return f"Deserialization error: {e}", 400

# Removed the endpoint to prevent SSRF vulnerability
# @app.get("/fetch")
# def fetch():
#     url = request.args.get("url", "http://127.0.0.1:22")
#     try:

#         r = requests.get(url, timeout=3, verify=False)
#         return (r.text[:2000] if r.text else str(r.status_code))
#     except Exception as e:
#         return f"Fetch error: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)