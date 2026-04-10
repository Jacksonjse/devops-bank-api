from flask import Flask, request, jsonify, g, send_from_directory
import sqlite3
import os

app = Flask(__name__, template_folder='templates', static_folder='templates')


@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response


@app.route('/', methods=['GET'])
def index():
    return send_from_directory('templates', 'index.html')


@app.route('/', methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path=''):
    return '', 204


DB_PATH = os.environ.get("DB_PATH", "bank.db")
FRAUD_THRESHOLD = 50000


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                flagged INTEGER NOT NULL DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()


@app.route("/account", methods=["POST"])
def create_account():
    data = request.get_json()
    account_id = data.get("account_id")
    name = data.get("name")
    if not account_id or not name:
        return jsonify({"error": "account_id and name are required"}), 400
    db = get_db()
    existing = db.execute(
        "SELECT * FROM accounts WHERE account_id = ?", (account_id,)
    ).fetchone()
    if existing:
        return jsonify({"error": "Account already exists"}), 409
    db.execute(
        "INSERT INTO accounts (account_id, name, balance) VALUES (?, ?, ?)",
        (account_id, name, 0),
    )
    db.commit()
    return jsonify({"message": "Account created", "account_id": account_id}), 201


@app.route("/deposit", methods=["POST"])
def deposit():
    data = request.get_json()
    account_id = data.get("account_id")
    amount = data.get("amount")
    if not account_id or amount is None:
        return jsonify({"error": "account_id and amount are required"}), 400
    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400
    db = get_db()
    account = db.execute(
        "SELECT * FROM accounts WHERE account_id = ?", (account_id,)
    ).fetchone()
    if not account:
        return jsonify({"error": "Account not found"}), 404
    flagged = 1 if amount > FRAUD_THRESHOLD else 0
    db.execute(
        "UPDATE accounts SET balance = balance + ? WHERE account_id = ?",
        (amount, account_id),
    )
    db.execute(
        "INSERT INTO transactions (account_id, type, amount, flagged) VALUES (?, ?, ?, ?)",
        (account_id, "deposit", amount, flagged),
    )
    db.commit()
    new_balance = db.execute(
        "SELECT balance FROM accounts WHERE account_id = ?", (account_id,)
    ).fetchone()["balance"]
    response = {"message": "Deposit successful", "new_balance": new_balance}
    if flagged:
        response["warning"] = f"Transaction flagged for fraud review (amount > {FRAUD_THRESHOLD})"
    return jsonify(response), 200


@app.route("/withdraw", methods=["POST"])
def withdraw():
    data = request.get_json()
    account_id = data.get("account_id")
    amount = data.get("amount")
    if not account_id or amount is None:
        return jsonify({"error": "account_id and amount are required"}), 400
    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400
    db = get_db()
    account = db.execute(
        "SELECT * FROM accounts WHERE account_id = ?", (account_id,)
    ).fetchone()
    if not account:
        return jsonify({"error": "Account not found"}), 404
    if account["balance"] < amount:
        return jsonify({"error": "Insufficient funds"}), 400
    flagged = 1 if amount > FRAUD_THRESHOLD else 0
    db.execute(
        "UPDATE accounts SET balance = balance - ? WHERE account_id = ?",
        (amount, account_id),
    )
    db.execute(
        "INSERT INTO transactions (account_id, type, amount, flagged) VALUES (?, ?, ?, ?)",
        (account_id, "withdraw", amount, flagged),
    )
    db.commit()
    new_balance = db.execute(
        "SELECT balance FROM accounts WHERE account_id = ?", (account_id,)
    ).fetchone()["balance"]
    response = {"message": "Withdrawal successful", "new_balance": new_balance}
    if flagged:
        response["warning"] = f"Transaction flagged for fraud review (amount > {FRAUD_THRESHOLD})"
    return jsonify(response), 200


@app.route("/balance/<account_id>", methods=["GET"])
def get_balance(account_id):
    db = get_db()
    account = db.execute(
        "SELECT * FROM accounts WHERE account_id = ?", (account_id,)
    ).fetchone()
    if not account:
        return jsonify({"error": "Account not found"}), 404
    return jsonify({
        "account_id": account_id,
        "name": account["name"],
        "balance": account["balance"],
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
