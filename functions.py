from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from gppt import GetPixivToken
import time
import json
import os
from urllib.parse import quote_plus
import matplotlib.pyplot as plt  # 追加
from matplotlib import rcParams #日本語対応化
rcParams['font.family'] = 'Meiryo'

USERNAME = "kn16sub@gmail.com"
PASSWORD = "KOUICHIkouichi0924"
COOKIE_FILE = "pixiv_cookies.json"
GRAPH_FILE = "static/result.png"  # グラフ画像の保存場所（必要に応じて調整）

def save_cookies(USERNAME,PASSWORD,headless):
    """Pixivに自動ログインして、クッキーを保存"""
    print("Pixivにログイン中...")
    try:
        gpt = GetPixivToken(username=USERNAME, password=PASSWORD, headless=headless)
        gpt.login()

        #セッションが活きているか確認
        if not gpt.driver.session_id:
            raise Exception("Selenium driver session is invalid.")

        # クッキー取得
        cookies = gpt.driver.get_cookies()
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)

        print("クッキー保存完了")
        #gpt.driver.quit() #gpptファイルのquite命令はコメントアウトして無効化してある
        gpt.driver.quit()
        return 1
    except (TimeoutException, ValueError, TypeError):
        return 0

def search_and_graph(search_word: str, headless=True):
    if not os.path.exists(COOKIE_FILE):
        raise FileNotFoundError("ログインクッキーが見つかりません。まず login_and_save_cookies() を実行してください。")

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,800")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.pixiv.net/")
        driver.delete_all_cookies()

        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass

        url_allages = f"https://www.pixiv.net/tags/{quote_plus(search_word)}/artworks?mode=safe&s_mode=s_tag"
        url_r18 = f"https://www.pixiv.net/tags/{quote_plus(search_word)}/artworks?mode=r18&s_mode=s_tag"
        
        results = []
        for url in (url_allages, url_r18):
            driver.get(url)

            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.sc-477e09dd-10.gEVgul"))
            )
            time.sleep(1)
            count_text = driver.find_element(By.CSS_SELECTOR, "span.sc-477e09dd-10.gEVgul").text
            count = int(count_text.replace(",", "").strip())
            print(f"『{search_word}』の検索件数: {count} 件") 
            results.append(count)
        results.append(sum(results))

    finally:
        driver.quit()

    try:
        rates = {
            'allages': results[0],
            'r18': results[1],
            'allages rate': results[0]/results[2]*100,
            'r18 rate': results[1]/results[2]*100,
            'total': results[2]
        }
    except ZeroDivisionError:
        return "error"

    # ここからグラフ生成 ----------------------------------------------------
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

    os.makedirs(os.path.dirname(GRAPH_FILE), exist_ok=True)  # ディレクトリなければ作る
    plt.savefig(GRAPH_FILE)
    plt.close()
    # --------------------------------------------------------------------

    # グラフのパスも返すと便利です
    return rates, GRAPH_FILE
