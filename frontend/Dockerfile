# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Build the application
# Pass VITE_API_URL as a build argument if needed by the build process
# ARG VITE_API_URL
# RUN VITE_API_URL=${VITE_API_URL} npm run build
RUN npm run build


# Production stage
FROM nginx:alpine

# Install gettext for envsubst
RUN apk update && apk add --no-cache gettext

# Copy the build output from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy the Nginx config template
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Expose port 80
EXPOSE 80

# Use envsubst to substitute environment variables in the config template
# and then start Nginx. The NGINX_SERVER_NAME variable will be passed
# via docker-compose environment section.
CMD ["/bin/sh", "-c", "envsubst '$${NGINX_SERVER_NAME}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
