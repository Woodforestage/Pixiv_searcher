# Playwright公式のPythonベースイメージを使用（Debian + Chromium等）
FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

# 作業ディレクトリの作成
WORKDIR /app

# Python依存パッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリの全ファイルをコピー
COPY . .

# Playwrightのブラウザと依存ライブラリをインストール
RUN playwright install --with-deps

# FlaskがListenするポート番号（RenderのPORT環境変数を参照）
EXPOSE 10000

# アプリの起動コマンド（gunicornでFlaskを起動）
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT:-10000}", "app:app"]
