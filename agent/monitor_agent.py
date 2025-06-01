#!/usr/bin/env python3
"""
Server Monitoring Agent
Collects system metrics and sends to central server
"""

import json
import time
import psutil
import requests
import socket
import logging
from datetime import datetime
from pathlib import Path

class MonitoringAgent:
    def __init__(self, config_path="config.json"):
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.server_name = self.config.get('server_name', socket.gethostname())
        
    def load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration
            return {
                "central_server": "http://localhost:5000",
                "server_name": socket.gethostname(),
                "collect_interval": 60,
                "retry_attempts": 3,
                "retry_delay": 10
            }
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/monitoring-agent.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def collect_metrics(self):
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Load average
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Process count
            process_count = len(psutil.pids())
            
            metrics = {
                'server_name': self.server_name,
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_avg_1m': load_avg[0],
                    'load_avg_5m': load_avg[1],
                    'load_avg_15m': load_avg[2]
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'processes': process_count
            }
            
            return metrics
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return None
    
    def send_metrics(self, metrics):
        """Send metrics to central server"""
        url = f"{self.config['central_server']}/api/metrics"
        
        for attempt in range(self.config['retry_attempts']):
            try:
                response = requests.post(
                    url,
                    json=metrics,
                    timeout=10,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    self.logger.info(f"Metrics sent successfully to {url}")
                    return True
                else:
                    self.logger.warning(f"Server returned status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.config['retry_attempts'] - 1:
                    time.sleep(self.config['retry_delay'])
        
        self.logger.error("Failed to send metrics after all retry attempts")
        return False
    
    def run(self):
        """Main monitoring loop"""
        self.logger.info(f"Starting monitoring agent for {self.server_name}")
        self.logger.info(f"Central server: {self.config['central_server']}")
        self.logger.info(f"Collection interval: {self.config['collect_interval']} seconds")
        
        while True:
            try:
                # Collect metrics
                metrics = self.collect_metrics()
                
                if metrics:
                    # Send to central server
                    self.send_metrics(metrics)
                else:
                    self.logger.error("Failed to collect metrics")
                
                # Wait for next collection
                time.sleep(self.config['collect_interval'])
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring agent stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                time.sleep(30)  # Wait before retrying

if __name__ == "__main__":
    agent = MonitoringAgent()
    agent.run()