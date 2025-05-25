from flask import Flask, request, render_template, redirect, url_for, session, flash, send_file
import datetime
import os
import io
from matplotlib import pyplot as plt, rcParams
from pixiv_searcher import login_and_save_cookies as csave, load_cookies_and_search as lcs

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # セッション用に設定してください

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
    message = ''

    # --- クッキー取得処理 ---
    if should_run_today() and not cookie_got:
        if request.method == 'POST' and 'login' in request.form:
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            if not username or not password:
                flash("ユーザー名とパスワードを入力してください", 'warning')
            else:
                result = csave(username, password, headless=True)
                if result == 0:
                    flash("ユーザーネームまたはパスワードが間違っています", 'error')
                else:
                    with open(LAST_RUN_PATH, 'w') as f:
                        f.write(datetime.date.today().isoformat())
                    session['cookie_got'] = True
                    cookie_got = True
                    flash("クッキーの取得が完了しました", 'success')
        return render_template('login.html')

    session['cookie_got'] = True  # すでに取得済み扱いに

    # --- 検索処理 ---
    if request.method == 'POST' and 'search' in request.form:
        search_words = request.form.get('search_words', '')
        if not search_words:
            flash("キャラクター名を入力してください", 'warning')
            return render_template('search.html', cookie_got=cookie_got)
        
        rates = lcs(search_words, headless=True)
        if rates == "error":
            flash("検索がうまくいきませんでした", 'error')
            return render_template('search.html', cookie_got=cookie_got)
        
        # グラフ作成
        rcParams['font.family'] = 'Meiryo'
        labels = ['健全絵', 'R-18']
        sizes = [rates['allages'], rates['r18']]
        colors = ['skyblue', 'lightcoral']

        fig, ax = plt.subplots()
        ax.pie(
            sizes,
            labels=labels,
            autopct=lambda p: f"{round(p * sum(sizes) / 100):,}件",
            startangle=90,
            colors=colors,
            wedgeprops=dict(width=0.45),
            pctdistance=0.75
        )
        ax.text(0, 0, f'健全絵：{rates["allages rate"]:.1f}%\nR18絵：{rates["r18 rate"]:.1f}%\n計 {rates["total"]} 件',
                ha='center', va='center', fontsize=14)
        ax.axis('equal')

        # 画像をメモリに保存してセッションに入れるか、一時ファイルに保存
        img_io = io.BytesIO()
        plt.savefig(img_io, format='png', bbox_inches='tight')
        img_io.seek(0)
        session['img_png'] = img_io.getvalue()  # バイト列をセッションに保存（注意: サイズ注意）

        # 検索結果もセッションに保存
        session['rates'] = rates
        session['search_words'] = search_words

        plt.close(fig)
        return redirect(url_for('result'))

    # 初回アクセスか、GETアクセス時
    return render_template('search.html', cookie_got=cookie_got)

@app.route('/result')
def result():
    rates = session.get('rates')
    search_words = session.get('search_words')
    img_png = session.get('img_png')

    if not rates or not img_png:
        return redirect(url_for('index'))

    return render_template('result.html', rates=rates, search_words=search_words)

@app.route('/plot.png')
def plot_png():
    img_png = session.get('img_png')
    if not img_png:
        return '', 404
    return send_file(io.BytesIO(img_png), mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
