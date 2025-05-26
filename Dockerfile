# Playwright 対応の公式 Python イメージ
FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

WORKDIR /app

# Python依存パッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリコードをコピー
COPY . .

# Playwrightのブラウザ（Chromium）を明示的にインストール、キャッシュの削除
ARG CACHEBUST=1　

RUN playwright install --with-deps

# Renderが使うポートを開放
EXPOSE 10000

# アプリを起動
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
