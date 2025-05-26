# ベースイメージとしてPython公式イメージを指定
FROM python:3.11-slim

# 環境変数の設定（Pythonのバッファリングを無効化、UTF-8設定）
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# 作業ディレクトリ作成
WORKDIR /app

# 必要なLinuxパッケージのインストール（Playwright用の依存含む）
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    git \
    unzip \
    xvfb \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxss1 \
    libasound2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm-dev \
    libpango-1.0-0 \
    libatk1.0-0 \
    libcups2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Pythonライブラリのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwrightのブラウザーをインストール
RUN playwright install --with-deps

# 必要ファイルをすべてコピー
COPY . .

# ポートの指定（Renderや他のPaaS向け）
EXPOSE 10000

# サーバー起動（PORTは環境変数から受け取る）
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT:-10000}", "app:app"]
