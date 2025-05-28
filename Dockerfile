# ベースイメージ
FROM python:3.11-slim

# システム依存関係インストール（Playwright用のブラウザ依存ライブラリ含む）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg libnss3 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libgtk-3-0 libasound2 libpangocairo-1.0-0 libatk1.0-0 libcups2 libdrm2 \
    libxss1 libxtst6 libxcb1 libxshmfence1 libpci3 libxfixes3 libdbus-1-3 libatspi2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ設定
WORKDIR /app

# Poetryやpipのアップグレード（任意）
RUN pip install --upgrade pip

# 依存パッケージをまとめてインストール
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Playwrightのブラウザをインストール
RUN playwright install --with-deps

# アプリのソースコードをコピー
COPY . /app

# Flaskのポート設定（Cloud Runは8080推奨）
ENV PORT 8080

# 環境変数の設定（例：Flask環境変数）
ENV FLASK_ENV=production

# 起動コマンド
CMD ["python", "app.py"]
