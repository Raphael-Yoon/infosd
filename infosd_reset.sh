#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 2. 깃허브 최신 코드 pull 시도
echo "Pulling latest code from origin master..."
if ! git pull origin master; then
    echo "ERROR: git pull failed (conflict or network error). Gunicorn will not be restarted." >&2
    exit 1
fi

# 3. 최신 코드 반영 후 서버 재시작
./infosd_start.sh
