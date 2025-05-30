from playwright.sync_api import sync_playwright
import os
from urllib.parse import quote_plus
import matplotlib.pyplot as plt
from matplotlib import rcParams
import db

rcParams['font.family'] = 'Meiryo'

GRAPH_FILE = "static/result.png"

def save_cookies(username, headless=False):
    """
    GUIブラウザでPixivにログインし、ユーザーがログインを手動で完了したら、
    自動的にCookieを取得してDBに保存する。

    Parameters:
        username (str): 対象ユーザー名
        headless (bool): ブラウザを非表示で開くかどうか（GUI必須なので通常False）

    Returns:
        int, list: 成功(1)/失敗(0), CookieリストまたはNone
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://accounts.pixiv.net/login")
        print("ブラウザでPixivのログイン画面が開きました。手動でログインしてください。")

        try:
            # ログイン完了判定：最大5分まで待つ
            page.wait_for_url("https://www.pixiv.net/*", timeout=5*60*1000)  # URLがpixivトップ等に変わるのを待つ
            # または
            # page.wait_for_selector("css=selector_for_logged_in_user_icon", timeout=5*60*1000)

            print("ログインが完了しました。Cookieを取得します。")

            cookies = context.cookies()
            # ここでDB保存関数呼び出し
            db.save_cookies_to_db(username, cookies)

            print("✅ CookieをDBに保存しました。")

        except TimeoutError:
            print("[ERROR] ログイン完了が確認できませんでした。")
            cookies = None

        finally:
            browser.close()

        if cookies:
            return 1, cookies
        else:
            return 0, None

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
