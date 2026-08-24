"""
[개발3팀 InfoSD] MySQL 'infosd' ➔ SQLite 백업 동기화 모듈
일일 백업 스크립트(backup_all.sh) 실행 시 MySQL의 infosd 데이터를 infosd.db(SQLite)로 스냅샷 백업합니다.
"""

import sys
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent
DEFAULT_SQLITE_PATH = BASE_DIR / "infosd.db"

if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from db_config import _parse_mysql_url, DATABASE_URL


def backup_infosd_to_sqlite(sqlite_path: Path = DEFAULT_SQLITE_PATH):
    import pymysql
    import pymysql.cursors

    config = _parse_mysql_url(DATABASE_URL)
    db_name = config["database"]

    try:
        mysql_conn = pymysql.connect(
            **config,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5,
        )
    except Exception as e:
        print(f"⚠️ [InfoSD Backup] MySQL 연결 불가 ({e}), 백업 스킵.")
        return

    sqlite_conn = sqlite3.connect(sqlite_path)
    s_cur = sqlite_conn.cursor()

    tables_order = [
        "isd_migration_history",
        "isd_companies",
        "isd_targets",
        "isd_questions",
        "isd_answers",
        "isd_evidence",
        "isd_sessions",
        "isd_submissions",
        "isd_answer_history",
        "ipd_users",
        "isd_user",
        "isd_user_company",
    ]

    try:
        with mysql_conn.cursor() as m_cur:
            for table in tables_order:
                m_cur.execute(f"SELECT * FROM `{table}`")
                rows = m_cur.fetchall()
                if not rows:
                    s_cur.execute(f"DELETE FROM `{table}`")
                    continue

                col_names = list(rows[0].keys())
                cols_str = ", ".join([f"`{c}`" for c in col_names])
                placeholders = ", ".join(["?"] * len(col_names))

                s_cur.execute(f"DELETE FROM `{table}`")
                values_list = []
                for r in rows:
                    values_list.append([
                        str(r[c]) if hasattr(r[c], "strftime") else r[c]
                        for c in col_names
                    ])

                s_cur.executemany(f"INSERT INTO `{table}` ({cols_str}) VALUES ({placeholders})", values_list)

        sqlite_conn.commit()
        print(f"✅ [InfoSD Backup] MySQL '{db_name}' ➔ SQLite 동기화 완료: 12개 테이블 백업 덤프 성공")
    finally:
        sqlite_conn.close()
        mysql_conn.close()


if __name__ == "__main__":
    backup_infosd_to_sqlite()
