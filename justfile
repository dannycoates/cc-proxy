# cc-proxy management commands

service := "cc-proxy"
user_service_dir := env("HOME") / ".config/systemd/user"
log_dir := env("HOME") / ".local/log/cc-proxy"

# List available commands
default:
    @just --list

# Install systemd user service
install:
    mkdir -p {{user_service_dir}}
    mkdir -p {{log_dir}}
    cp cc-proxy.service {{user_service_dir}}/
    systemctl --user daemon-reload
    @echo "Installed. Run 'just start' to start the service."

# Uninstall systemd user service
uninstall: stop
    systemctl --user disable {{service}} || true
    rm -f {{user_service_dir}}/cc-proxy.service
    systemctl --user daemon-reload
    @echo "Uninstalled."

# Start the service
start:
    systemctl --user start {{service}}

# Stop the service
stop:
    systemctl --user stop {{service}}

# Restart the service
restart:
    systemctl --user restart {{service}}

# Show service status
status:
    @systemctl --user status {{service}}

# Enable service to start on login
enable:
    systemctl --user enable {{service}}

# Disable service from starting on login
disable:
    systemctl --user disable {{service}}

# Tail the log (follow mode)
log:
    tail -f {{log_dir}}/cc-proxy.log

# Show recent log entries
log-recent lines="50":
    tail -n {{lines}} {{log_dir}}/cc-proxy.log

# Run locally (not as service)
run port="8080":
    ./cc-proxy {{port}}
