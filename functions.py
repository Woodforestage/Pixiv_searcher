from playwright.sync_api import sync_playwright
import os
from urllib.parse import quote_plus
import matplotlib.pyplot as plt
from matplotlib import rcParams
import db

rcParams['font.family'] = 'Meiryo'

GRAPH_FILE = "static/result.png"

def save_cookies(username, password, headless=True):
    """PixivにPlaywrightでログインしてクッキー取得し、そのままdictで返す"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--no-sandbox"])
        context = browser.new_context()

        page = context.new_page()
        page.goto("https://accounts.pixiv.net/login")

        try:
            page.fill('input[type="text"]', username)
            page.fill('input[type="password"]', password)
            page.click('button[type="submit"]')

            page.wait_for_url("https://www.pixiv.net/*", timeout=10000)

            cookies = context.cookies()

            browser.close()
            return 1, cookies

        except Exception as e:
            print("ログイン失敗:", e)
            browser.close()
            return 0, None


def search_and_graph(username, search_word: str, headless=True):
    """DBからユーザーのクッキーを取得し、検索・グラフ生成"""
    cookies = db.get_latest_cookies(username)
    if not cookies:
        return "error"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--no-sandbox"])
        context = browser.new_context()

        # クッキーをセット（Playwrightのdict形式なのでそのまま使う）
        context.add_cookies(cookies)

        page = context.new_page()
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
