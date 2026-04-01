#!/bin/bash
cd "$(dirname "$0")"
sudo python3 print-server.py &
SERVER_PID=$!
trap "sudo kill $SERVER_PID 2>/dev/null; wait $SERVER_PID 2>/dev/null" EXIT
sleep 1
xdg-open index.html
wait
