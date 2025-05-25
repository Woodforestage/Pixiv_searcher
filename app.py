from flask import Flask, request, render_template, redirect, url_for, session, flash, send_file
import datetime
import os
from functions import save_cookies as scs, search_and_graph as lcs  # グラフも含む関数に変更

app = Flask(__name__)
app.secret_key = 'your-secret-key'

DATA_DIR = 'data'
LAST_RUN_PATH = os.path.join(DATA_DIR, 'last_run.txt')

os.makedirs(DATA_DIR, exist_ok=True)

def should_run_today():
    today = datetime.date.today().isoformat()
    if not os.path.exists(LAST_RUN_PATH):
        return True
    with open(LAST_RUN_PATH, 'r') as f:
        return f.read().strip() != today

@app.route('/', methods=['GET', 'POST'])
def index():
    cookie_got = session.get('cookie_got', False)

    # --- クッキー取得処理 ---
    if should_run_today() and not cookie_got:
        if request.method == 'POST' and 'login' in request.form:
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            if not username or not password:
                flash("ユーザー名とパスワードを入力してください", 'warning')
            else:
                result = scs(username, password, headless=False)
                if result == 0:
                    flash("ユーザーネームまたはパスワードが間違っています", 'error')
                else:
                    with open(LAST_RUN_PATH, 'w') as f:
                        f.write(datetime.date.today().isoformat())
                    session['cookie_got'] = True
                    cookie_got = True
                    flash("クッキーの取得が完了しました", 'success')
        return render_template('login.html')

    session['cookie_got'] = True

    # --- 検索処理 ---
    if request.method == 'POST' and 'search' in request.form:
        search_words = request.form.get('search_words', '')
        if not search_words:
            flash("キャラクター名を入力してください", 'warning')
            return render_template('search.html', cookie_got=cookie_got)

        result = lcs(search_words, headless=False)
        if result == "error":
            flash("検索がうまくいきませんでした", 'error')
            return render_template('search.html', cookie_got=cookie_got)

        rates, graph_path = result
        session['graph_path'] = graph_path  # 後で表示用
        
        return render_template('result.html', cookie_got=cookie_got, result=rates, search_words=search_words)

    return render_template('search.html', cookie_got=cookie_got)

@app.route('/graph')
def graph():
    graph_path = session.get('graph_path')
    if not graph_path or not os.path.exists(graph_path):
        return '', 404
    return send_file(graph_path, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) #Renderでの起動用

