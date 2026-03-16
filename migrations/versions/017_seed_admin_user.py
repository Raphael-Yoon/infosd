"""
기본 어드민 계정 시드 삽입
- snowball2727@naver.com (Admin)
"""
import uuid


def upgrade(conn):
    existing = conn.execute(
        "SELECT id FROM isd_user WHERE user_email = 'snowball2727@naver.com'"
    ).fetchone()
    if not existing:
        conn.execute('''
            INSERT INTO isd_user (id, user_name, user_email, is_admin)
            VALUES (?, ?, ?, 1)
        ''', (str(uuid.uuid4()), '관리자', 'snowball2727@naver.com'))
        conn.commit()


def downgrade(conn):
    conn.execute("DELETE FROM isd_user WHERE user_email = 'snowball2727@naver.com'")
    conn.commit()
