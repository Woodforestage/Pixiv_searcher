from flask import Flask, request, render_template, redirect, url_for, session, flash, send_file
import os
from functions import save_cookies, search_and_graph
import db  # 先ほどのdb.pyをimport

app = Flask(__name__)
app.secret_key = 'd3tz9s82f99ep25s'

# 起動時にDB初期化（あればスキップ）
db.init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    username = session.get('username')
    cookie_exists = False

    if username:
        # DBにクッキーがあるか確認
        cookies = db.get_latest_cookies(username)
        cookie_exists = cookies is not None

    if not cookie_exists:
        # Cookie無ければログイン処理
        if request.method == 'POST' and 'login' in request.form:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            if not username or not password:
                flash("ユーザー名とパスワードを入力してください", 'warning')
                return render_template('login.html')

            # Playwrightでログインしてクッキー取得
            result, cookies = save_cookies(username, password, headless=True)
            if result == 0:
                flash("ユーザーネームまたはパスワードが間違っています", 'error')
                return render_template('login.html')

            # クッキーをDBに保存
            db.save_cookies(username, cookies)

            # セッションにユーザー名保存
            session['username'] = username

            flash("クッキーの取得が完了しました", 'success')
            return redirect(url_for('index'))

        # GETやPOST(login以外)はログインフォーム表示
        return render_template('login.html')

    # クッキーあるなら検索処理へ
    if request.method == 'POST' and 'search' in request.form:
        search_words = request.form.get('search_words', '').strip()
        if not search_words:
            flash("キャラクター名を入力してください", 'warning')
            return render_template('search.html', cookie_got=True)

        result = search_and_graph(username, search_words, headless=True)
        if result == "error":
            # Cookie無効かエラーならログアウト扱い
            db.delete_cookies(username)
            session.pop('username', None)
            flash("Cookieが無効になったか、検索中に問題が発生しました。再度ログインしてください。", 'error')
            return render_template('login.html')

        rates, graph_path = result
        session['graph_path'] = graph_path

        return render_template('result.html', cookie_got=True, result=rates, search_words=search_words)

    # GETは検索フォーム表示
    return render_template('search.html', cookie_got=True)


@app.route('/graph')
def graph():
    graph_path = session.get('graph_path')
    if not graph_path or not os.path.exists(graph_path):
        return '', 404
    return send_file(graph_path, mimetype='image/png')


@app.route('/logout')
def logout():
    username = session.get('username')
    if username:
        db.delete_cookies(username)
    session.clear()
    flash("ログアウトしました。", "info")
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
