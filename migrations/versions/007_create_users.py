"""
사용자 인증 테이블 생성 및 기본 관리자 계정 시딩

기본 로그인 정보:
  아이디: admin
  비밀번호: infosd2024  (최초 로그인 후 변경 권장)
"""
from werkzeug.security import generate_password_hash


def upgrade(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ipd_users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT    NOT NULL UNIQUE,
            password   TEXT    NOT NULL,
            is_active  INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    conn.execute(
        'INSERT OR IGNORE INTO ipd_users (username, password) VALUES (?, ?)',
        ('admin', generate_password_hash('infosd2024'))
    )


def downgrade(conn):
    conn.execute('DROP TABLE IF EXISTS ipd_users')
