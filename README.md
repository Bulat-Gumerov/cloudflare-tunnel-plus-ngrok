# Project Overview

This project encompasses configurations and scripts for deploying a Docker-based web application, enabling accessibility even when behind NAT without requiring port-forwarding, TLS or a VPN setup. The solution hinges on Cloudflared serving as the primary tunneling tool, with Ngrok as a fallback option. While Cloudflared operation does not necessitate an account, Ngrok usage mandates an account along with an NGROK_AUTHTOKEN env. variable. Additionally, the project incorporates a Python script for dynamically updating Prometheus blackbox exporter configuration based on container logs.

## Files Included

- **docker-compose.yml**: Defines the services, networks, and volumes for the Docker setup.
- **nginx.conf**: NGINX configuration file for proxying requests to the web service.
- **update-blackbox.py**: Python script for updating Prometheus configuration based on container logs.

## Components

### Web Service

A dummy web app running on port 8080.

### NGINX

Used for proxying requests and adding custom header for Ngrok only. It listens on port 80.

### Cloudflared

A primary tool by Cloudflare for creating a secure tunnel to the web service. It's configured to expose dummy app on port 80.

### NGROK

Backup tool that used for exposing local servers to the internet securely, but it has less free limits than Cloudflared. It's configured to expose NGINX on port 80.

### Prometheus blackbox exporter(optional)

Monitoring tool for collecting and querying HTTP metrics. You can use the script to dynamically update its configuration based on container logs with the new tunnel URLs.

## Usage

1. Ensure Docker and Docker compose are installed.
2. Clone this repository.
3. Modify configurations or script as needed.
4. Execute `docker-compose up -d` to initiate the services.
5. (optional) Run `./update-blackbox.py` to automatically update the Prometheus configuration. You can also set up a cron job for periodic updates.
6. (optional) Utilize `./update-blackbox.py --clear` to purge URLs from the Prometheus configuration as necessary.
7. (optional) Monitor services via the Prometheus UI or Grafana.
