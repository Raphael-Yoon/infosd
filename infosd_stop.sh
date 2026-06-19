#!/bin/bash

# 1. PID 파일이 존재하면 해당 프로세스 종료
PID_FILE="/home/raphael/Dev/pythons/infosd/infosd.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping infosd Gunicorn process (PID: $PID)..."
        kill -9 $PID
    fi
    rm "$PID_FILE"
else
    # PID 파일이 없을 경우 패턴 매칭으로 종료 (다른 Gunicorn 프로세스 간섭 최소화)
    echo "No PID file found. Terminating via process pattern..."
    pkill -9 -f "gunicorn.*infosd:app"
fi

echo "infosd Gunicorn processes terminated."
