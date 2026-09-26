#!/usr/bin/env bash
# Starts the Core API (port 5000), the Lecturer API (port 5001), and serves
# the front-end (port 8000).
set -e
cd "$(dirname "$0")"

echo "=============================================="
echo "  ExamPortal - starting up"
echo "=============================================="
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found on this computer."
  echo "Install it from https://www.python.org/downloads/ and run this script again."
  exit 1
fi

if ! python3 -c "import flask" >/dev/null 2>&1; then
  echo "Installing the backend's only requirement, Flask..."
  if ! python3 -m pip install --quiet --disable-pip-version-check Flask; then
    echo
    echo "Could not install Flask automatically. Try running this manually:"
    echo "  python3 -m pip install Flask"
    exit 1
  fi
  echo "Flask installed."
  echo
fi

( cd backend/core-api && python3 app.py ) &
CORE_PID=$!
( cd backend/lecturer-api && python3 app.py ) &
LECTURER_PID=$!
trap 'kill $CORE_PID $LECTURER_PID 2>/dev/null' EXIT

# open the browser once the servers have had a moment to start
( sleep 2
  if command -v open >/dev/null 2>&1; then open "http://localhost:8000" >/dev/null 2>&1
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "http://localhost:8000" >/dev/null 2>&1
  fi
) &

echo "ExamPortal is running at http://localhost:8000"
echo "Keep this window open while you use it. Press Ctrl+C to stop."
echo
python3 -m http.server 8000
