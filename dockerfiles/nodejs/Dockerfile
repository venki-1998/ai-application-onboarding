FROM node:20-alpine
# Set working directory
WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install --only=production

# Copy source code
COPY . .

# Expose app port
EXPOSE 3000

# Run the application
CMD ["npm", "start"]
