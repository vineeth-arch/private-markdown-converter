#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

PID_FILE=".streamlit/app.pid"
HEALTH_URL="http://localhost:8501/_stcore/health"
APP_URL="http://localhost:8501"

mkdir -p .streamlit

PYTHON_BIN=""
LAUNCHED_PID=""
CREATED_PID_FILE=0
HANDOFF_COMPLETE=0

show_error() {
  local message="$1"
  osascript -e "display dialog \"$message\" buttons {\"OK\"} default button \"OK\" with icon stop" >/dev/null 2>&1 || true
}

cleanup_on_exit() {
  if [[ "$HANDOFF_COMPLETE" -eq 1 ]]; then
    return
  fi

  if [[ -n "$LAUNCHED_PID" ]] && kill -0 "$LAUNCHED_PID" >/dev/null 2>&1; then
    kill "$LAUNCHED_PID" >/dev/null 2>&1 || true
  fi

  if [[ "$CREATED_PID_FILE" -eq 1 && -f "$PID_FILE" ]]; then
    rm -f "$PID_FILE"
  fi
}

trap cleanup_on_exit EXIT

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  show_error "Python 3 was not found. Create .venv or install python3, then try again."
  exit 1
fi

if ! "$PYTHON_BIN" -m streamlit --version >/dev/null 2>&1; then
  show_error "Streamlit is not installed for the selected Python environment. Activate your environment and run pip install -r requirements.txt."
  exit 1
fi

if [[ -f "$PID_FILE" ]]; then
  EXISTING_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$EXISTING_PID" ]] && kill -0 "$EXISTING_PID" >/dev/null 2>&1; then
    open "$APP_URL" >/dev/null 2>&1 || true
    HANDOFF_COMPLETE=1
    exit 0
  fi
  rm -f "$PID_FILE"
fi

nohup "$PYTHON_BIN" -m streamlit run app.py >/dev/null 2>&1 &
LAUNCHED_PID="$!"
printf '%s\n' "$LAUNCHED_PID" > "$PID_FILE"
CREATED_PID_FILE=1

for _ in {1..10}; do
  if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
    open "$APP_URL" >/dev/null 2>&1 || true
    HANDOFF_COMPLETE=1
    exit 0
  fi

  if ! kill -0 "$LAUNCHED_PID" >/dev/null 2>&1; then
    show_error "Private Markdown Converter stopped before it finished starting. Please try again."
    exit 1
  fi

  sleep 0.5
done

show_error "Private Markdown Converter did not become ready within 5 seconds. Please try again."
exit 1
