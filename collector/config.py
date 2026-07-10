# Machine Collector Configuration

API_URL = "http://127.0.0.1:8000/api/v1/events/"
API_KEY = "machine-dev-key-change-me"
POLL_SEC = 1

# Enabled modules
ENABLE_WINDOW = True
ENABLE_IDLE = True
ENABLE_MUSIC = True

# Window module
WINDOW_TITLE_MAX = 200

# Idle module
IDLE_THRESHOLD_SEC = 300  # 5 minutes

# Queue settings
QUEUE_MAX_SIZE = 100
SENDER_INTERVAL_SEC = 10
SENDER_MAX_RETRIES = 3
