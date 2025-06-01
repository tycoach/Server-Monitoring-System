#!/bin/bash
# Monitoring Agent Installation Script

set -e

INSTALL_DIR="/opt/monitoring"
SERVICE_NAME="monitoring-agent"
USER="monitoring"

echo "Installing Server Monitoring Agent..."

# Create monitoring user
if ! id "$USER" &>/dev/null; then
    echo "Creating monitoring user..."
    sudo useradd -r -s /bin/false $USER
fi

# Create installation directory
echo "Creating installation directory..."
sudo mkdir -p $INSTALL_DIR
sudo cp *.py $INSTALL_DIR/
sudo cp *.json $INSTALL_DIR/
sudo chown -R $USER:$USER $INSTALL_DIR
sudo chmod +x $INSTALL_DIR/monitor_agent.py

# Install Python dependencies
echo "Installing Python dependencies..."
sudo pip3 install psutil requests

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Server Monitoring Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/monitor_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create log directory
sudo mkdir -p /var/log
sudo touch /var/log/monitoring-agent.log
sudo chown $USER:$USER /var/log/monitoring-agent.log

# Reload systemd and enable service
echo "Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

echo "Installation completed!"
echo ""
echo "To start the service: sudo systemctl start $SERVICE_NAME"
echo "To check status: sudo systemctl status $SERVICE_NAME"
echo "To view logs: sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Don't forget to update the config.json with your central server IP!"