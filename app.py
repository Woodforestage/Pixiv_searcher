from flask import Flask, request, jsonify, send_file, session
from flask_cors import CORS
from functions import save_cookies, search_and_graph, is_cookie_valid
from db import init_db, get_latest_cookie, save_cookie_to_db
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

init_db()  # DB初期化

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    headless = data.get("headless", True)

    if not username or not password:
        return jsonify({"message": "username and password required"}), 400

    # Pixivログイン & cookie取得
    status, cookie = save_cookies(username, password, headless)
    if status != "success":
        return jsonify({"message": "login failed"}), 401

    # DBに保存
    save_cookie_to_db(username, cookie)

    # セッションに保存（任意）
    session["username"] = username

    return jsonify({"message": "login success"})


@app.route("/search")
def search():
    username = session.get("username")
    if not username:
        return jsonify({"message": "not logged in"}), 401

    # DBから最新cookie取得
    cookie = get_latest_cookie(username)
    if not cookie or not is_cookie_valid(cookie):
        return jsonify({"message": "cookie invalid or expired"}), 401

    query = request.args.get("query")
    if not query:
        return jsonify({"message": "query param required"}), 400

    # 検索実行・グラフ生成
    search_and_graph(query, cookie)

    # 画像返却（キャッシュ防止のため時間クエリ付与）
    return send_file("static/result.png", mimetype="image/png")


if __name__ == "__main__":
    # Render環境では0.0.0.0、PORTは環境変数から取得推奨
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
