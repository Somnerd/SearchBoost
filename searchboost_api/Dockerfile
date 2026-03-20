FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install --production

COPY . .

# Ensure we don't bring in dev .env by accident if it exists in context, 
# although compose will override it.
RUN rm -f .env

EXPOSE 3001

CMD ["node", "src/app.js"]
