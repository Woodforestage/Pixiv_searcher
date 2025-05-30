from flask import Flask, request, render_template, redirect, url_for, session, flash
import db  # DB操作用のモジュール（先のsqlite管理関数群）
import os
from functions import save_cookies as scs, search_and_graph as sag, is_cookie_valid


app = Flask(__name__)
app.secret_key = 'd3tz9s82f99ep25s'
headless = True

#Debug config
debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'#Anaconda Prompt 環境変数：FLASK_DEBUG=true
port_setter=8080
if debug_mode:
    port_setter=5000 #デバックモードではポート5000を使う
    headless=False
    print('Debug Mode : ON')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if not username:
            flash("ユーザー名を入力してください", 'warning')
            return render_template('username.html')

        session['username'] = username

        # DBからクッキーを取得（JSON文字列ならjson.loadsで辞書に変換）
        cookie_json = db.get_latest_cookies(username)
        if cookie_json:
            try:
                cookies = json.loads(cookie_json)
            except Exception as e:
                flash("クッキーの読み込みに失敗しました", 'warning')
                session['cookie_got'] = False
                return redirect(url_for('login'))

            # クッキーの有効判定
            if is_cookie_valid(cookies):
                session['cookie_got'] = True
                return redirect(url_for('search'))
            else:
                flash("クッキーは無効です。再ログインしてください。", 'warning')
                session['cookie_got'] = False
                return redirect(url_for('login'))

        else:
            flash("Cookieが存在しません。ログインしてください。", 'warning')
            session['cookie_got'] = False
            return redirect(url_for('login'))

    # GET時はユーザー名入力フォーム
    return render_template('username.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    username = session.get('username', '')
    if not username:
        return redirect(url_for('index'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        if not password:
            flash("パスワードを入力してください", 'warning')
            return render_template('login.html', username=username)

        result = scs(username, password, headless)
        if result == 0:
            flash("ユーザーネームまたはパスワードが間違っています", 'error')
            return render_template('login.html', username=username)

        session['cookie_got'] = True
        flash("クッキーの取得が完了しました", 'success')
        return redirect(url_for('search'))

    return render_template('login.html', username=username)


@app.route('/search', methods=['GET', 'POST'])
def search():
    cookie_got = session.get('cookie_got', False)
    username = session.get('username', '')
    if not cookie_got or not username:
        flash("まずユーザー名を入力し、ログインしてください", 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        search_words = request.form.get('search_words', '').strip()
        if not search_words:
            flash("検索キーワードを入力してください", 'warning')
            return render_template('search.html')

        # sag関数にusernameとsearch_wordsを渡す想定
        result = sag(username, search_words, headless)
        if result == "error":
            session.pop('cookie_got', None)
            flash("Cookieが無効か、検索中に問題が発生しました。再度ログインしてください。", 'error')
            return redirect(url_for('login'))

        rates, graph_path = result
        session['graph_path'] = graph_path
        return render_template('result.html', result=rates, search_words=search_words)

    return render_template('search.html')


@app.route('/graph')
def graph():
    graph_path = session.get('graph_path')
    if not graph_path or not os.path.exists(graph_path):
        return '', 404
    return send_file(graph_path, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', port_setter)))
