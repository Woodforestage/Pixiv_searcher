from playwright.sync_api import sync_playwright
import os
from urllib.parse import quote_plus
import matplotlib.pyplot as plt
from matplotlib import rcParams
import db
import re

print("Ver 6/06 1:19")

rcParams['font.family'] = 'IPAGothic'

GRAPH_FILE = "static/result.png"

def save_cookies(username, password, headless):
    """
    Playwrightを用いてPixivにログインし、Cookieを保存する。
    Apple認証ページへのリダイレクトも検出する。

    Returns:
        str, list | None: 'success', 'error', 'apple_redirect_error', Cookieリスト or None
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-webauthn", "--disable-features=WebAuthentication"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/114.0.0.0 Safari/537.36",
            locale="ja-JP"
        )

        page = context.new_page()

        # webdriver偽装スクリプト挿入
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        try:
            page.goto("https://accounts.pixiv.net/login?return_to=https%3A%2F%2Fwww.pixiv.net%2F")
            page.wait_for_selector('input[type="text"][autocomplete*="username"]', timeout=8000)

            # typeで入力（delayを入れて人間っぽく）
            page.type('input[type="text"]', username, delay=100)
            page.wait_for_timeout(500)
            page.type('input[type="password"]', password, delay=100)
            page.wait_for_timeout(500)

            # ログインボタンをクリック（念のためセレクタを確認）
            page.click('button[type="submit"]')

            page.wait_for_load_state('networkidle')

            # Apple認証ページへのリダイレクト確認
            if re.search(r"appleid\.apple\.com", page.url):
                print("[ERROR] Apple認証ページへのリダイレクトを検出")
                browser.close()
                return 'apple_redirect_error', None

            # ログイン成功判定（ユーザーアイコンが表示されるか）
            try:
                page.wait_for_selector("div.user-icon", timeout=7000)
                cookies = context.cookies()
                db.save_cookies_to_db(username, cookies)
                print("DBにクッキーを保存しました")
                browser.close()
                return 'success', cookies
            except Exception:
                print("[ERROR] ユーザーアイコンが見つかりません。ログインに失敗した可能性があります。")
                browser.close()
                return 'error', None

        except Exception as e:
            print(f"[ERROR] Pixivログイン失敗: {e}")
            browser.close()
            return 'error', None




def search_and_graph(username, search_word: str, headless=True):
    """DBからユーザーのクッキーを取得し、検索・グラフ生成"""
    cookies = db.get_latest_cookies(username)
    if not cookies:
        print("Cookieが保存されていません")
        return "error"

    cookies = filter_pixiv_cookies(cookies)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--no-sandbox"])

        context = browser.new_context()
        context.add_cookies(cookies)
        page = context.new_page()
        page.goto("https://www.pixiv.net/")

        # ページ内にログイン状態を示す要素があるか確認（任意）
        try:
            page.wait_for_selector("div.user-icon", timeout=5000)
            print("ログイン状態を確認しました")
        except:
            print("ログインしていません")

        urls = {
            "allages": f"https://www.pixiv.net/tags/{quote_plus(search_word)}/artworks?mode=safe&s_mode=s_tag",
            "r18": f"https://www.pixiv.net/tags/{quote_plus(search_word)}/artworks?mode=r18&s_mode=s_tag"
        }

        counts = {}
        for key, url in urls.items():
            page.goto(url)
            try:
                page.wait_for_selector("span.sc-477e09dd-10.gEVgul", timeout=10000)
                count_text = page.query_selector("span.sc-477e09dd-10.gEVgul").inner_text()
                counts[key] = int(count_text.replace(",", "").strip())
            except Exception as e:
                print(f"{key}の取得に失敗:", e)
                counts[key] = 0

        browser.close()

        total = counts["allages"] + counts["r18"]
        if total == 0:
            return "error"

        rates = {
            'allages': counts["allages"],
            'r18': counts["r18"],
            'allages rate': counts["allages"] / total * 100,
            'r18 rate': counts["r18"] / total * 100,
            'total': total
        }

        # グラフ生成
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

        os.makedirs(os.path.dirname(GRAPH_FILE), exist_ok=True)
        plt.savefig(GRAPH_FILE)
        plt.close(fig)

        return rates, GRAPH_FILE


def filter_pixiv_cookies(cookies):
    filtered = []
    for c in cookies:
        if 'pixiv.net' in c['domain']:
            # domainを.pixiv.netに統一
            c['domain'] = '.pixiv.net'
            filtered.append(c)
    return filtered


def is_cookie_valid(cookies):
    # Pixivはセッションが24時間程度で切れるため、簡易的に有効期限を見る
    import time
    now = time.time()
    for c in cookies:
        if c["name"] == "PHPSESSID" and c.get("expires", 0) > now:
            return True
    return False