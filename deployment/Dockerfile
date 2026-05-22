FROM python:3.9-slim

WORKDIR /app

# 安裝系統基本依賴（如果需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴配置並安裝
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案其餘檔案
COPY backend/src /app/src

# 暴露 FastAPI 連接埠
EXPOSE 8000

# 預設啟動指令 (在 compose 中會以 volumes 掛載並 reload 運行)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
