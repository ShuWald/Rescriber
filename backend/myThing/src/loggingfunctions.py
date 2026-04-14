# Logging utilities for the backend server.

import time
import os

default_log = None


def set_log(base_log_file_path=None):
    """Set the main log file path used by log_to_file.

    Default format is Log/<timestamp>/log_main.log.
    Also ensures legacy log.txt exists in top-level Log directory.
    """
    global default_log
    if base_log_file_path is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        base_log_file_path = os.path.join("Log", timestamp, "log_main.log")

    root, ext = os.path.splitext(base_log_file_path)
    if not ext:
        base_log_file_path = f"{base_log_file_path}.log"

    default_log = base_log_file_path
    log_dir = os.path.dirname(default_log)
    os.makedirs(log_dir, exist_ok=True)

    # Ensure legacy-style log.txt exists in top-level Log directory.
    root_log_dir = "Log"
    os.makedirs(root_log_dir, exist_ok=True)
    legacy_log_path = os.path.join(root_log_dir, "log.txt")
    if not os.path.exists(legacy_log_path):
        with open(legacy_log_path, "a") as f:
            f.write("This directory contains all generated logs")

    return default_log


# Helps determing the route log paths
def _get_route_log_path(main_log_path, route):

    directory = os.path.dirname(main_log_path)
    filename = os.path.basename(main_log_path)
    stem, ext = os.path.splitext(filename)
    if "main" in stem:
        route_stem = stem.replace("main", route)
    else:
        route_stem = f"{stem}_{route}"
    return os.path.join(directory, f"{route_stem}{ext or '.log'}")


# Log a message to a file, with defaults for printing and route-specific logging
    """ Args:
        message: The log message.
        log_file: Optional override for the log file path.
        print_too: Whether to also print to console (default True).
        route: Optional route name to also log to route-specific file.
    """
def log_to_file(message, log_file=None, print_too=True, route=None):

    active_log = log_file or default_log or set_log()
    os.makedirs(os.path.dirname(active_log), exist_ok=True)
    with open(active_log, "a") as f:
        f.write(message + "\n")

    if route:
        route_log_path = _get_route_log_path(active_log, route)
        with open(route_log_path, "a") as rf:
            rf.write(message + "\n")

    if print_too:
        print(message)
    return True
