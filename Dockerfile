# Playwright対応の公式ベース
FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ブラウザと依存をPlaywrightで一括インストール
RUN playwright install --with-deps

EXPOSE 10000

CMD ["gunicorn", "--bind", "0.0.0.0:${PORT:-10000}", "app:app"]
