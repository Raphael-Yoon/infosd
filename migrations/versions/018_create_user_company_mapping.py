"""
사용자-회사 매핑 테이블 생성
- 일반 사용자는 배정된 회사만 접근 가능
- Admin은 제한 없이 전체 접근
"""


def upgrade(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS isd_user_company (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL REFERENCES isd_user(id),
            company_id  TEXT NOT NULL REFERENCES isd_companies(id),
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, company_id)
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_isd_user_company_user ON isd_user_company(user_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_isd_user_company_company ON isd_user_company(company_id)')
    conn.commit()


def downgrade(conn):
    conn.execute('DROP TABLE IF EXISTS isd_user_company')
    conn.commit()
