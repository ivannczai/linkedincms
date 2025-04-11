# Deployment Guide: Docker Compose on Ubuntu 22.04

This guide outlines the steps to deploy the Winning Sales Content Hub application using Docker Compose on a fresh Ubuntu 22.04 server (e.g., a DigitalOcean Droplet).

**Assumptions:**

*   You have SSH access to your Ubuntu 22.04 server.
*   You have a domain name you want to point to this application (optional, but needed for HTTPS).
*   You have already created the LinkedIn Application and have your Client ID and Secret.
*   Your GitHub repository (`https://github.com/ivannczai/linkedincms.git`) is **public**.

## Step 1: Server Preparation (Connect via SSH)

Log in to your server via SSH:
```bash
ssh your_user@your_server_ip
```

## Step 2: Install Prerequisites

Update package lists and install Docker, Docker Compose plugin, and Git.

```bash
# Update package list
sudo apt update
sudo apt upgrade -y

# Install prerequisites for Docker repository
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine and Compose plugin
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to the docker group to run docker commands without sudo (requires logout/login)
sudo usermod -aG docker ${USER}
echo "Please log out and log back in for Docker group changes to take effect."
# exit # Log out now
# ssh your_user@your_server_ip # Log back in

# Verify Docker installation
docker --version
docker compose version

# Install Git
sudo apt install -y git
```
*Note: You need to log out and log back in after adding your user to the `docker` group.*

## Step 3: Clone the Application Repository

Clone the code from your public GitHub repository.

```bash
git clone https://github.com/ivannczai/linkedincms.git
cd linkedincms # Navigate into the project directory
```

## Step 4: Configure LinkedIn Application

*   Go to your application settings on the [LinkedIn Developer Portal](https://developer.linkedin.com/).
*   Under "Auth" -> "OAuth 2.0 settings", find the "Redirect URLs" section.
*   **Add** the following URL, replacing `<your_server_ip_or_domain>` with the actual public IP address or domain name of your server:
    `http://<your_server_ip_or_domain>:8000/api/v1/linkedin/connect/callback`
    *(Note: Even though the frontend is served on port 80, the callback goes directly to the backend container, which exposes port 8000. If you set up HTTPS later, you'll need to update this to `https://...`)*

## Step 5: Create and Configure the `.env` File

Create the `.env` file in the project root (`linkedincms/`) and populate it with your **production** settings. **Do not commit this file.**

```bash
nano .env
```

Paste the following content into the editor, **replacing placeholder values with your actual production settings**:

```dotenv
# Database (For Docker Compose, use service name 'db' as host)
DATABASE_URL=postgresql://postgres:<YOUR_SECURE_DB_PASSWORD>@db:5432/content_hub
# Variables used by the 'db' service in docker-compose.yml
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<YOUR_SECURE_DB_PASSWORD> # Use a strong password
POSTGRES_DB=content_hub

# Security
SECRET_KEY=<YOUR_VERY_LONG_RANDOM_SECURE_SECRET_KEY> # Generate a strong random key
ACCESS_TOKEN_EXPIRE_MINUTES=10080 # 7 days (Adjust as needed)

# Backend (CORS - IMPORTANT: Restrict to your frontend domain)
BACKEND_CORS_ORIGINS='["http://<your_server_ip_or_domain>"]' # e.g., '["https://app.yourdomain.com"]'

# Frontend (API URL - Used during build)
VITE_API_URL=http://backend:8000 # Internal URL for build process

# Initial Admin User (Used by entrypoint.sh in backend container)
FIRST_SUPERUSER_EMAIL=<your_admin_email@example.com>
FIRST_SUPERUSER_PASSWORD=<YOUR_SECURE_ADMIN_PASSWORD> # Use a strong password

# LinkedIn Integration
LINKEDIN_CLIENT_ID=<YOUR_LINKEDIN_CLIENT_ID>
LINKEDIN_CLIENT_SECRET=<YOUR_LINKEDIN_CLIENT_SECRET>
# Redirect URI MUST match what you configured in LinkedIn App settings (Step 4)
LINKEDIN_REDIRECT_URI=http://<your_server_ip_or_domain>:8000/api/v1/linkedin/connect/callback

# Frontend URL (Used for redirects from backend)
FRONTEND_URL_BASE=http://<your_server_ip_or_domain> # e.g., https://app.yourdomain.com
```

*   **Replace all placeholders** like `<YOUR_SECURE_DB_PASSWORD>`, `<YOUR_VERY_LONG_RANDOM_SECURE_SECRET_KEY>`, `<your_admin_email@example.com>`, `<YOUR_SECURE_ADMIN_PASSWORD>`, `<YOUR_LINKEDIN_CLIENT_ID>`, `<YOUR_LINKEDIN_CLIENT_SECRET>`, and `<your_server_ip_or_domain>`.
*   Use strong, unique passwords and keys.
*   Ensure `BACKEND_CORS_ORIGINS` and `FRONTEND_URL_BASE` use the correct public URL/IP/domain where your app will be accessed. If using HTTPS later, update these to `https://...`.
*   Ensure `LINKEDIN_REDIRECT_URI` exactly matches the one added in the LinkedIn Developer Portal.

Save the file (Ctrl+X, then Y, then Enter in `nano`).

## Step 6: Build and Run the Application

Navigate to the project root directory (`linkedincms/`) if you aren't already there. Run Docker Compose:

```bash
docker compose up --build -d
```

*   `--build`: Builds the images based on the Dockerfiles (needed on first run or after code changes).
*   `-d`: Runs the containers in detached mode (in the background).

Docker Compose will:
1.  Build the frontend image (running `npm install` and `npm run build`).
2.  Build the backend image (running `poetry install`).
3.  Start the `db` container.
4.  Start the `backend` container (which will wait for the DB, run `alembic upgrade head`, and create the superuser via `entrypoint.sh`).
5.  Start the `frontend` container (Nginx).

You can check the logs to monitor startup:
```bash
docker compose logs -f backend
docker compose logs -f frontend
```
Press Ctrl+C to stop following logs.

## Step 7: Access the Application

Open your web browser and navigate to:
`http://<your_server_ip_or_domain>`

You should see the application's login page. You can log in using the `FIRST_SUPERUSER_EMAIL` and `FIRST_SUPERUSER_PASSWORD` you set in the `.env` file.

## Step 8: (Optional) Configure DNS

If you have a custom domain name, configure its DNS records (usually an `A` record) to point to your server's public IP address (`your_server_ip`). DNS changes can take time to propagate.

## Step 9: (Recommended) Setup HTTPS with Let's Encrypt

For production, running over HTTPS is essential. A common way to achieve this with this setup is using Certbot with the Nginx plugin. This involves:

1.  Stopping the running `frontend` container (`docker compose stop frontend`).
2.  Installing Certbot and the Nginx plugin on the host server (`sudo apt install certbot python3-certbot-nginx`).
3.  Running Certbot to obtain a certificate for your domain (`sudo certbot --nginx -d yourdomain.com`). Certbot will modify the Nginx configuration (potentially one running on the host, or you might need to adapt it for the containerized Nginx).
4.  Adjusting the `frontend/nginx.conf` and potentially `docker-compose.override.yml` to handle SSL certificates and HTTPS traffic (e.g., mounting certificate volumes, listening on port 443).
5.  Updating `FRONTEND_URL_BASE` and `LINKEDIN_REDIRECT_URI` in your `.env` file and LinkedIn App settings to use `https://`.
6.  Restarting the containers (`docker compose up -d --force-recreate frontend`).

*This HTTPS setup is more involved and specific instructions depend on your exact Nginx configuration preferences.*

---

Your application should now be deployed and running using Docker Compose on your Ubuntu server.
