#!/usr/bin/env python3
"""
ReconX - Core Utilities
Helper functions used across all modules.
"""

import os
import re
import shutil
import socket
import subprocess
from datetime import datetime


def tool_exists(name):
    return shutil.which(name) is not None


def tool_version(name):
    for flag in ("--version", "-version", "-V", "-v"):
        try:
            result = subprocess.run(
                [name, flag],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = (result.stdout or result.stderr or "").strip()
            if output:
                return output.splitlines()[0][:120]
        except Exception:
            continue
    return "unknown"


def check_tools(tools):
    status = {}
    for t in tools:
        status[t] = tool_exists(t)
    return status


def sanitize_name(value):
    if value is None:
        return "unknown"
    value = value.strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = value.split("/")[0]
    value = value.split(":")[0]
    value = re.sub(r"[^a-zA-Z0-9._-]", "_", value)
    value = value.replace(".", "_")
    value = re.sub(r"_+", "_", value)
    return value.strip("_") or "unknown"


def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def human_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def resolve_target(target):
    try:
        return socket.gethostbyname(target)
    except Exception:
        return None


def is_valid_domain(value):
    if not value or len(value) > 253:
        return False
    pattern = re.compile(
        r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
        r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*"
        r"\.[A-Za-z]{2,63}$"
    )
    return bool(pattern.match(value))


def is_valid_ip(value):
    try:
        socket.inet_aton(value)
        return value.count(".") == 3
    except Exception:
        return False


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def write_file(path, content):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [ln.strip() for ln in f if ln.strip()]


def dedupe(items):
    seen = set()
    result = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(item.strip())
    return result
