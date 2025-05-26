# Playwright対応の公式Pythonイメージ（Chromiumの依存も含む）
FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

# 作業ディレクトリの設定
WORKDIR /app

# 依存パッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードをコピー
COPY . .

# PlaywrightでChromiumブラウザを明示的にインストール
RUN playwright install chromium

# ポート開放（Renderが10000ポートを使う）
EXPOSE 10000

# アプリの起動（RenderではPORT環境変数を使う）
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]

