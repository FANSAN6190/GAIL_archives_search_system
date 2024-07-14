#!/bin/bash
PID=$(lsof -t -i:9000)
if [ -n "$PID" ]; then
    echo "Killing process on port 9000 with PID: $PID"
    kill -9 $PID
else
    echo "No process running on port 9000"
fi