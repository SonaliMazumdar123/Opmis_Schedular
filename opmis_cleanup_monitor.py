#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import glob
import subprocess

BASE_DIR = "/export/home/users/bmadmin/bmadmin/Automation_Testing"
SCRIPT_PATH = os.path.join(BASE_DIR, "D2D_Delete_Old_Log.ksh")
LOG_DIR = os.path.join(BASE_DIR, "log")
RUN_LOG = os.path.join(LOG_DIR, "opmis_cleanup_monitor.log")
LOCK_FILE = os.path.join(BASE_DIR, "opmis_cleanup_monitor.lock")

MIN_OK_KB = 45
MAX_OK_KB = 46

CHECK_INTERVAL_SECONDS = 60
MAX_WAIT_SECONDS = 30 * 60
MAX_RETRIES = 2


def write_log(message):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s\n" % (ts, message)
    try:
        f = open(RUN_LOG, "a")
        f.write(line)
        f.close()
    except:
        pass
    sys.stdout.write(line)
    sys.stdout.flush()


def create_lock():
    if os.path.exists(LOCK_FILE):
        write_log("Lock file exists. Another run may already be in progress: %s" % LOCK_FILE)
        return 0
    try:
        f = open(LOCK_FILE, "w")
        f.write(str(os.getpid()))
        f.close()
        return 1
    except Exception, e:
        write_log("Unable to create lock file: %s" % str(e))
        return 0


def remove_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass


def get_file_size_kb(path):
    try:
        size_bytes = os.path.getsize(path)
        return size_bytes / 1024
    except:
        return -1


def list_cleanup_files():
    pattern = os.path.join(LOG_DIR, "store_log_cleanup_*.log")
    return glob.glob(pattern)


def find_new_file(before_files, start_time):
    files = list_cleanup_files()
    candidates = []

    for f in files:
        if f not in before_files:
            try:
                mtime = os.path.getmtime(f)
                if mtime >= start_time:
                    candidates.append((mtime, f))
            except:
                pass

    if not candidates:
        return None

    candidates.sort()
    return candidates[-1][1]


def file_contains_completed(path):
    try:
        f = open(path, "r")
        content = f.read()
        f.close()
        if "Completed at:" in content:
            return 1
    except:
        pass
    return 0


def run_cleanup_script():
    write_log("Running cleanup script: %s" % SCRIPT_PATH)
    try:
        cmd = "cd %s && ./D2D_Delete_Old_Log.ksh" % BASE_DIR
        rc = subprocess.call(cmd, shell=True)
        write_log("Cleanup script exited with return code: %s" % str(rc))
        return rc
    except Exception, e:
        write_log("Failed to run cleanup script: %s" % str(e))
        return 999


def wait_for_target(target_file):
    start = time.time()

    while 1:
        elapsed = time.time() - start
        if elapsed > MAX_WAIT_SECONDS:
            write_log("Timeout reached while waiting for file completion/size: %s" % target_file)
            return 0

        if os.path.exists(target_file):
            size_kb = get_file_size_kb(target_file)
            completed = file_contains_completed(target_file)

            write_log("Current file: %s | size=%s KB | completed=%s" %
                      (target_file, str(size_kb), str(completed)))

            if completed and size_kb >= MIN_OK_KB and size_kb <= MAX_OK_KB:
                write_log("Validation successful. File completed and size is within %s-%s KB." %
                          (str(MIN_OK_KB), str(MAX_OK_KB)))
                return 1
        else:
            write_log("Expected output file not found yet: %s" % target_file)

        time.sleep(CHECK_INTERVAL_SECONDS)


def attempt_once(attempt_no):
    write_log("========== Attempt %s started ==========" % str(attempt_no))

    before_files = list_cleanup_files()
    start_time = time.time()

    rc = run_cleanup_script()

    if rc != 0:
        write_log("Cleanup script returned non-zero exit code.")

    target_file = None
    find_deadline = time.time() + 300

    while time.time() < find_deadline:
        target_file = find_new_file(before_files, start_time)
        if target_file:
            break
        write_log("Waiting for new store_log_cleanup file to be created...")
        time.sleep(10)

    if not target_file:
        write_log("No new cleanup log file was created for this attempt.")
        return 0

    write_log("Monitoring new cleanup log file: %s" % target_file)
    return wait_for_target(target_file)


def main():
    if not create_lock():
        return 1

    try:
        attempt = 1
        while attempt <= (MAX_RETRIES + 1):
            success = attempt_once(attempt)

            if success:
                write_log("SUCCESS: Cleanup verified on attempt %s" % str(attempt))
                return 0

            if attempt < (MAX_RETRIES + 1):
                write_log("Validation failed. Re-running cleanup script.")
            else:
                write_log("FAILED: Cleanup did not meet validation after all attempts.")
                return 1

            attempt = attempt + 1

        return 1
    finally:
        remove_lock()


if __name__ == "__main__":
    sys.exit(main())
