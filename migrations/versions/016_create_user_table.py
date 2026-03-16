"""
사용자 인증 테이블 생성
- isd_user : 시스템 접근 계정 (관리자가 직접 발급)
"""


def upgrade(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS isd_user (
            id                  TEXT PRIMARY KEY,
            user_name           TEXT NOT NULL,
            user_email          TEXT NOT NULL UNIQUE,
            is_admin            INTEGER NOT NULL DEFAULT 0,
            otp_code            TEXT,
            otp_expires_at      TIMESTAMP,
            otp_attempts        INTEGER NOT NULL DEFAULT 0,
            effective_start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            effective_end_date  TIMESTAMP,
            last_login_at       TIMESTAMP,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()


def downgrade(conn):
    conn.execute('DROP TABLE IF EXISTS isd_user')
    conn.commit()
