# Liquidity App Server Management

When the application is deployed on Ubuntu, it is managed as a background service via `systemd`. This ensures that the application starts automatically when the server boots and restarts if it crashes.

The name of the service is: `liquidity-dashboard.service`

## 🔄 Restarting the Server

If you have pulled new code from GitHub or made changes to the files on the server (like modifying `config.py`), you need to restart the service for the changes to take effect:

```bash
sudo systemctl restart liquidity-dashboard
```

## 📊 Viewing the Server Logs

If the application isn't working or you want to see the live output (like error messages or print statements), you can tail the logs using `journalctl`:

```bash
# View the last 50 lines of logs
sudo journalctl -u liquidity-dashboard -n 50

# Follow the logs live (press Ctrl+C to exit)
sudo journalctl -u liquidity-dashboard -f
```

## 🛑 Stopping and Starting

If you need to temporarily take the dashboard down:

```bash
# Stop the server
sudo systemctl stop liquidity-dashboard

# Start it back up
sudo systemctl start liquidity-dashboard
```

## 🔍 Checking Status

To see if the server is currently running, stopped, or if it failed to start, check its status:

```bash
sudo systemctl status liquidity-dashboard
```

This will show you the uptime, the process ID, and the last few log messages.
