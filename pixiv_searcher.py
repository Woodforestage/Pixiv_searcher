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


USERNAME = "kn16sub@gmail.com"
PASSWORD = "KOUICHIkouichi0924"
COOKIE_FILE = "pixiv_cookies.json"


def login_and_save_cookies(USERNAME,PASSWORD,headless):
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
        


def load_cookies_and_search(search_word: str, headless=True):
    """保存済みクッキーを使用して検索＆総件数を取得"""
    if not os.path.exists(COOKIE_FILE):
        raise FileNotFoundError("ログインクッキーが見つかりません。まず login_and_save_cookies() を実行してください。")

    # Chromeのオプション
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,800")

    driver = webdriver.Chrome(options=options)

    try:
        # 一度Pixivトップにアクセスしてクッキーをセット可能な状態にする
        driver.get("https://www.pixiv.net/")
        driver.delete_all_cookies()

        # クッキー読み込み
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass

        # 検索URLにアクセス
        url_allages = f"https://www.pixiv.net/tags/{quote_plus(search_word)}/artworks?mode=safe&s_mode=s_tag"  # 全年齢（健全）
        url_r18 = f"https://www.pixiv.net/tags/{quote_plus(search_word)}/artworks?mode=r18&s_mode=s_tag"  # R-18（18禁）
        
        results=[]
        for url in (url_allages, url_r18):
            driver.get(url)

            # 件数の要素が出るまで待つ（CSSセレクタは変わる可能性あり）
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.sc-477e09dd-10.gEVgul"))
            )
            time.sleep(1)
            # 件数を取得
            count_text = driver.find_element(By.CSS_SELECTOR, "span.sc-477e09dd-10.gEVgul").text
            count = int(count_text.replace(",", "").strip()) #検索条件に合致する作品数が格納される変数
            print(f"『{search_word}』の検索件数: {count} 件") 
            results.append(count)
        results.append(sum(results))
        #results=[number of allages, number of r18, total]
            

    finally:
        driver.quit()
        try:
            rates={'allages':results[0],'r18':results[1],'allages rate':results[0]/results[2]*100,
                   'r18 rate':results[1]/results[2]*100, 'total':results[2]}
        except ZeroDivisionError:
            return "error"
    return rates


"""
if __name__ == "__main__":
    # ステップ① ログイン＆クッキー保存（初回 or 期限切れ時のみ）
    login_and_save_cookies(headless=False)
    # ステップ② 検索とスクレイピング（何度でも可能）
    search_term = "ブルアカ　シュポガキ"
    result=load_cookies_and_search(search_term, headless=False)
    print(result)
"""
