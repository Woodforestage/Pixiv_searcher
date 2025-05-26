from playwright.sync_api import sync_playwright
import time
import json
import os
from urllib.parse import quote_plus
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.family'] = 'Meiryo'

COOKIE_FILE = "pixiv_cookies.json"
GRAPH_FILE = "static/result.png"

def save_cookies(username, password, headless=True):
    """PixivにPlaywrightでログインしてクッキー保存"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()

        page = context.new_page()
        page.goto("https://accounts.pixiv.net/login")

        try:
            page.fill('input[type="text"]', username)
            page.fill('input[type="password"]', password)
            page.click('button[type="submit"]')

            page.wait_for_url("https://www.pixiv.net/*", timeout=10000)

            cookies = context.cookies()
            with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)

            browser.close()
            return 1

        except Exception as e:
            print("ログイン失敗:", e)
            browser.close()
            return 0

def search_and_graph(search_word: str, headless=True):
    if not os.path.exists(COOKIE_FILE):
        raise FileNotFoundError("ログインクッキーが見つかりません")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()

        # クッキーを読み込んでPixivドメインに設定
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
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
