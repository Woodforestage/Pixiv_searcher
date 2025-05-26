from flask import Flask, request, render_template, redirect, url_for, session, flash, send_file
import os
from functions import save_cookies as scs, search_and_graph as sag  # グラフも含む関数に変更

app = Flask(__name__)
app.secret_key = 'your-secret-key'

@app.route('/', methods=['GET', 'POST'])
def index():
    cookie_got = session.get('cookie_got', False)

    if not cookie_got:
        # まだCookie取れてなければログイン処理
        if request.method == 'POST' and 'login' in request.form:
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            if not username or not password:
                flash("ユーザー名とパスワードを入力してください", 'warning')
                return render_template('login.html')
            
            result = scs(username, password, headless=True)
            if result == 0:
                flash("ユーザーネームまたはパスワードが間違っています", 'error')
                return render_template('login.html')
            
            # Cookie取得成功
            session['cookie_got'] = True
            flash("クッキーの取得が完了しました", 'success')
            return redirect(url_for('index'))  # 取得完了したらリダイレクト

        # GETアクセスやPOST(login以外)はログインフォーム表示
        return render_template('login.html')

    # cookie_got == True なら検索処理へ
    if request.method == 'POST' and 'search' in request.form:
        search_words = request.form.get('search_words', '')
        if not search_words:
            flash("キャラクター名を入力してください", 'warning')
            return render_template('search.html', cookie_got=True)

        result = sag(search_words, headless=True)
        if result == "error":
            # ログアウト処理
            session.pop('cookie_got', None)  # セッションからcookie情報削除
            flash("Cookieが無効になったか、検索中に問題が発生しました。再度ログインしてください。", 'error')
            return render_template('login.html')
                    
        rates, graph_path = result
        session['graph_path'] = graph_path

        return render_template('result.html', cookie_got=True, result=rates, search_words=search_words)

    # GETアクセスは検索フォーム表示
    return render_template('search.html', cookie_got=True)


@app.route('/graph')
def graph():
    graph_path = session.get('graph_path')
    if not graph_path or not os.path.exists(graph_path):
        return '', 404
    return send_file(graph_path, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
