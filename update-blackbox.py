#!/usr/bin/env python3
import docker
import yaml
import argparse
from urllib.parse import urlparse

# Initialize the Docker client
client = docker.from_env()

# Function to check if a container is running
def is_container_running(container_name):
    try:
        container = client.containers.get(container_name)
        return container.status == 'running'
    except docker.errors.NotFound:
        return False

# Function to get the logs of a container
def get_container_logs(container_name):
    try:
        container = client.containers.get(container_name)
        logs = container.logs(tail=100).decode('utf-8')  # Get the last 100 lines of logs
        return logs
    except docker.errors.NotFound:
        return ""

# Function to extract the last URL from logs
def extract_last_url(logs, url_patterns):
    last_url = None
    for line in logs.splitlines():
        for pattern in url_patterns:
            if pattern in line:
                url = extract_url_from_line(line)
                if url and any(url_pattern in url for url_pattern in url_patterns):
                    last_url = url
    return last_url

# Function to extract and clean URLs from log lines
def extract_url_from_line(line):
    words = line.split()
    for word in words:
        if word.startswith('http://') or word.startswith('https://'):
            try:
                result = urlparse(word)
                if all([result.scheme, result.netloc]):
                    return word
            except ValueError:
                continue
    return None

# Function to clear specific URLs from the Prometheus configuration file
def clear_urls_from_config(config_file_path, url_patterns):
    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)
    
    updated = False
    for job in config['scrape_configs']:
        if job['job_name'] == 'blackbox':
            static_configs = job.get('static_configs', [])
            for static_config in static_configs:
                targets = static_config.get('targets', [])
                original_targets = targets.copy()
                for pattern in url_patterns:
                    targets = [url for url in targets if pattern not in url]
                if targets != original_targets:
                    updated = True
                static_config['targets'] = targets
    
    if updated:
        with open(config_file_path, 'w') as file:
            yaml.safe_dump(config, file)
        print("Prometheus configuration cleared and updated.")
    else:
        print("No URLs were found to clear in the Prometheus configuration.")

# Main script logic
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Prometheus configuration with URLs found in container logs.")
    parser.add_argument('--clear', action='store_true', help="Clear previously found URLs from the Prometheus configuration.")
    args = parser.parse_args()

    config_file_path = '/home/user/docker-monitoring-stack-gpnc/configs/prometheus/prometheus.yml'
    url_patterns = ['trycloudflare.com', 'ngrok-free.app']

    if args.clear:
        clear_urls_from_config(config_file_path, url_patterns)
    else:
        # Containers to check
        containers = ['cloudflared_tunnel', 'webapp_ngrok_1']
        found_urls = []

        # Check if containers are running and get their logs
        for container in containers:
            if is_container_running(container):
                logs = get_container_logs(container)
                last_url = extract_last_url(logs, url_patterns)
                if last_url:
                    found_urls.append(last_url)
                print(f"Container {container} is running.")
            else:
                print(f"Container {container} is not running.")

        # Proceed only if at least one URL is found
        if found_urls:
            # Check if Prometheus container is running
            if is_container_running('prometheus'):
                print("Prometheus container is running.")
            else:
                print("Prometheus container is not running.")
                prometheus_logs = get_container_logs('prometheus')
                print("Prometheus logs:\n", prometheus_logs)
                exit()

            # Load the configuration file
            with open(config_file_path, 'r') as file:
                config = yaml.safe_load(file)

            # Update the blackbox exporter job with the new URLs
            updated = False
            for job in config['scrape_configs']:
                if job['job_name'] == 'blackbox':
                    static_configs = job.get('static_configs', [])
                    targets = set()
                    for static_config in static_configs:
                        targets.update(static_config.get('targets', []))
                    
                    for url in found_urls:
                        if url not in targets:
                            targets.add(url)
                            updated = True
                    
                    job['static_configs'] = [{'targets': list(targets)}]

            # Write the updated configuration back to the file
            if updated:
                with open(config_file_path, 'w') as file:
                    yaml.safe_dump(config, file)

                # Restart the Prometheus container to apply changes
                prometheus_container = client.containers.get('prometheus')
                prometheus_container.restart()
                print("Prometheus configuration updated and container restarted.")
            else:
                print("No updates made to the Prometheus configuration.")
        else:
            print("No URLs found in the logs of example or sample containers.")
