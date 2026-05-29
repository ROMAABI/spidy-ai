import socket
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

NET = config["network"]


def is_online() -> bool:
    try:
        socket.setdefaulttimeout(NET["timeout"])
        socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        ).connect(("1.1.1.1", 53))
        return True
    except Exception:
        return False
