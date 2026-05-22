FROM node:18-alpine

WORKDIR /app

# 複製 package.json 安裝依賴
COPY package.json ./
RUN npm install

# 暴露 Vite 埠口
EXPOSE 3000

# 啟動開發伺服器（在 compose 中掛載 volumes 實現熱重載）
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
