import streamlit as st
import datetime
from pixiv_searcher import login_and_save_cookies as csave, load_cookies_and_search as lcs
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 初期化（状態の保持）
if "cookie_got" not in st.session_state:
    st.session_state.cookie_got = False

st.title("R18 比率検索WEB")
    
#＜一日一回のクッキーの取得＞
def should_run_today():
    today = datetime.date.today().isoformat()
    try:
        with open("last_run.txt", "r") as f:
            return f.read().strip() != today
    except FileNotFoundError:
        return True

# クッキー取得処理
if should_run_today() and not st.session_state.cookie_got:
    st.write("今日は初回アクセスなのでクッキーを取得します")
    USERNAME = st.text_input('ID:', placeholder="example@example.com")
    PASSWORD = st.text_input('PASS:', type="password")

    if st.button("ログインしてクッキーを取得"):
        if USERNAME and PASSWORD:
            if csave(USERNAME, PASSWORD, headless=True) == 0:
                st.error("ユーザーネームまたはパスワードが間違っています")
            else:
                with open("last_run.txt", "w") as f:
                    f.write(datetime.date.today().isoformat())
                st.session_state.cookie_got = True
                st.success("クッキーの取得が完了しました")
        else:
            st.warning("ユーザー名とパスワードを入力してください")

else:
    st.write("今日はすでにクッキーを取得済みです")
    st.session_state.cookie_got = True  # すでに取得済み扱いに

# 検索処理（クッキー取得済みのときだけ実行）
if st.session_state.cookie_got:
    st.write("こちらではキャラクター名を入力することでR18作品の比率を調べることができます")
    search_words = st.text_input('キャラ名', placeholder="キーワード")
    if st.button("検索"):
        # Pixiv検索
        rates = lcs(search_words, headless=True)
        if rates=="error":
            st.error("検索がうまくいきませんでした")
        #グラフ表示
        # 日本語フォントを指定（例: Windows の "Meiryo"）
        rcParams['font.family'] = 'Meiryo'
        
        labels = ['健全絵', 'R-18']
        sizes = [rates['allages'], rates['r18']]
        colors = ['skyblue', 'lightcoral']

        # グラフ描画
        fig, ax = plt.subplots()
        ax.pie(
            sizes,
            labels=labels,
            autopct=lambda p: f"{round(p * sum(sizes) / 100):,}件",
            startangle=90,
            colors=colors,
            wedgeprops=dict(width=0.45),  # ドーナツの厚み
            pctdistance=0.75
        )

        # 円の中にテキストを追加
        ax.text(0, 0, f'健全絵：{rates["allages rate"]:.1f}%\nR18絵：{rates["r18 rate"]:.1f}%\n計 {rates["total"]} 件',
                ha='center', va='center', fontsize=14)

        # 正円にする
        ax.axis('equal')
        
        st.pyplot(fig)
        
        #st.write(f"健全絵：{rates['allages']}件、比率: {rates['allages rate']:.1f}％")
        #st.write(f"R18絵：{rates['r18']}件、比率: {rates['r18 rate']:.1f}％")


