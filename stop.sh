#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

PID_FILE=".streamlit/app.pid"

show_message() {
  local message="$1"
  if [[ "${PMC_SUPPRESS_STOP_UI:-0}" == "1" ]]; then
    return
  fi

  if [[ -t 1 ]]; then
    printf '%s\n' "$message"
  else
    osascript -e "display dialog \"$message\" buttons {\"OK\"} default button \"OK\"" >/dev/null 2>&1 || true
  fi
}

if [[ ! -f "$PID_FILE" ]]; then
  show_message "App is not running."
  exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"
if [[ -z "$PID" ]]; then
  rm -f "$PID_FILE"
  show_message "App is not running."
  exit 0
fi

if ! kill -0 "$PID" >/dev/null 2>&1; then
  rm -f "$PID_FILE"
  show_message "App is not running."
  exit 0
fi

kill "$PID" >/dev/null 2>&1 || true

for _ in {1..6}; do
  if ! kill -0 "$PID" >/dev/null 2>&1; then
    rm -f "$PID_FILE"
    show_message "App stopped."
    exit 0
  fi
  sleep 0.5
done

kill -9 "$PID" >/dev/null 2>&1 || true
rm -f "$PID_FILE"
show_message "App stopped."
