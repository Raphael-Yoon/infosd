#!/bin/bash

# 1. 기존에 돌고 있는 infosd 관련 Gunicorn 프로세스만 종료 (PID 파일 활용)
PID_FILE="/home/raphael/Dev/pythons/infosd/infosd.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping existing infosd Gunicorn process (PID: $PID)..."
        kill -9 $PID
    fi
    rm "$PID_FILE"
fi

# 혹시 모를 잔여 프로세스 정리 (패턴 매칭)
pkill -f "gunicorn.*infosd:app"

# 2. 포트가 확실히 풀리도록 대기
sleep 1

# 3. 127.0.0.1:5003번 포트로 백그라운드 구동 (PID 파일 지정)
echo "Starting Gunicorn server on port 5003..."
nohup /home/raphael/Dev/pythons/.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5003 --pid "$PID_FILE" infosd:app > flask.log 2>&1 &

# 4. 결과 출력
echo "------------------------------------------------"
echo "infosd Gunicorn server started successfully on port 5003!"
echo "Logs are being written to flask.log"
echo "------------------------------------------------"
