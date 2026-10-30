"""Show the current UTC time in the Worker sandbox."""
from datetime import datetime, timezone


def run(data, configuration):
    now = datetime.now(timezone.utc)
    return {'utc': now.isoformat(timespec='seconds').replace('+00:00', 'Z'), 'unix_seconds': int(now.timestamp())}
