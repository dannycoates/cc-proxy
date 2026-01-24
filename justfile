# cc-proxy management commands

log_dir := "/var/log/cc-proxy"
service := "cc-proxy"

# List available commands
default:
    @just --list

# Install systemd service and logrotate config
install:
    sudo mkdir -p {{log_dir}}
    sudo chown {{env("USER")}}:{{env("USER")}} {{log_dir}}
    sudo cp cc-proxy.service /etc/systemd/system/
    sudo cp cc-proxy.logrotate /etc/logrotate.d/cc-proxy
    sudo systemctl daemon-reload
    @echo "Installed. Run 'just start' to start the service."

# Uninstall systemd service and logrotate config
uninstall: stop
    sudo systemctl disable {{service}} || true
    sudo rm -f /etc/systemd/system/cc-proxy.service
    sudo rm -f /etc/logrotate.d/cc-proxy
    sudo systemctl daemon-reload
    @echo "Uninstalled. Log directory {{log_dir}} preserved."

# Start the service
start:
    sudo systemctl start {{service}}

# Stop the service
stop:
    sudo systemctl stop {{service}}

# Restart the service
restart:
    sudo systemctl restart {{service}}

# Show service status
status:
    @systemctl status {{service}}

# Enable service to start on boot
enable:
    sudo systemctl enable {{service}}

# Disable service from starting on boot
disable:
    sudo systemctl disable {{service}}

# Tail the log (follow mode)
log:
    tail -f {{log_dir}}/cc-proxy.log

# Show recent log entries
log-recent lines="50":
    tail -n {{lines}} {{log_dir}}/cc-proxy.log

# Run locally (not as service)
run port="8080":
    ./cc-proxy {{port}}
