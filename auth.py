"""
infosd 인증 모듈
이메일 OTP 기반 로그인, login_required 데코레이터
"""
import random
import string
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for
from db_config import get_db


def generate_otp():
    """6자리 숫자 OTP 코드 생성"""
    return ''.join(random.choices(string.digits, k=6))


def find_user_by_email(email):
    """이메일로 활성 사용자 조회"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with get_db() as conn:
        row = conn.execute('''
            SELECT * FROM isd_user
            WHERE user_email = ?
              AND effective_start_date <= ?
              AND (effective_end_date IS NULL OR effective_end_date >= ?)
        ''', (email, now, now)).fetchone()
        return dict(row) if row else None


def send_otp(user_email):
    """OTP 생성 후 DB 저장 및 이메일 발송"""
    user = find_user_by_email(user_email)
    if not user:
        return False, "등록되지 않은 사용자입니다."

    otp_code = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=5)

    with get_db() as conn:
        conn.execute('''
            UPDATE isd_user
            SET otp_code = ?, otp_expires_at = ?, otp_attempts = 0
            WHERE user_email = ?
        ''', (otp_code, expires_at.strftime('%Y-%m-%d %H:%M:%S'), user_email))
        conn.commit()

    try:
        from infosd_mail import send_gmail
        subject = "[정보보호공시] 로그인 인증 코드"
        body = f"""안녕하세요 {user['user_name']}님,

로그인 인증 코드입니다.

인증 코드: {otp_code}

이 코드는 5분간 유효합니다.
본인이 요청하지 않았다면 이 메일을 무시하세요.

정보보호공시 시스템
"""
        send_gmail(user_email, subject, body)
        return True, "인증 코드가 이메일로 전송되었습니다."
    except Exception as e:
        return False, f"이메일 발송에 실패했습니다. ({e})"


def verify_otp(email, otp_code):
    """OTP 검증. 성공 시 (True, user_dict), 실패 시 (False, 오류메시지)"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with get_db() as conn:
        row = conn.execute('''
            SELECT * FROM isd_user
            WHERE user_email = ?
              AND effective_start_date <= ?
              AND (effective_end_date IS NULL OR effective_end_date >= ?)
        ''', (email, now, now)).fetchone()

        if not row:
            return False, "사용자를 찾을 수 없습니다."

        user = dict(row)

        if not user.get('otp_expires_at'):
            return False, "인증 코드를 먼저 요청해 주세요."

        if datetime.now() > datetime.fromisoformat(user['otp_expires_at']):
            return False, "인증 코드가 만료되었습니다. 다시 요청해 주세요."

        if user['otp_attempts'] >= 3:
            return False, "인증 시도 횟수를 초과했습니다. 새로운 코드를 요청하세요."

        if user['otp_code'] == otp_code:
            conn.execute('''
                UPDATE isd_user
                SET otp_code = NULL, otp_expires_at = NULL, otp_attempts = 0,
                    last_login_at = CURRENT_TIMESTAMP
                WHERE user_email = ?
            ''', (email,))
            conn.commit()
            return True, user
        else:
            conn.execute('''
                UPDATE isd_user SET otp_attempts = otp_attempts + 1 WHERE user_email = ?
            ''', (email,))
            conn.commit()
            remaining = 3 - (user['otp_attempts'] + 1)
            return False, f"인증 코드가 틀렸습니다. (남은 시도: {remaining}회)"


def get_current_user():
    """세션에서 현재 로그인 사용자 반환"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    with get_db() as conn:
        row = conn.execute('SELECT * FROM isd_user WHERE id = ?', (user_id,)).fetchone()
        return dict(row) if row else None


def login_required(f):
    """로그인 필수 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login.login_page'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """어드민 전용 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login.login_page'))
        user = get_current_user()
        if not user or not user.get('is_admin'):
            return "접근 권한이 없습니다.", 403
        return f(*args, **kwargs)
    return decorated


def create_user(user_name, user_email, is_admin=False):
    """새 사용자 생성 (어드민 전용)"""
    with get_db() as conn:
        existing = conn.execute(
            'SELECT id FROM isd_user WHERE user_email = ?', (user_email,)
        ).fetchone()
        if existing:
            return False, "이미 등록된 이메일입니다."
        conn.execute('''
            INSERT INTO isd_user (id, user_name, user_email, is_admin)
            VALUES (?, ?, ?, ?)
        ''', (str(uuid.uuid4()), user_name, user_email, 1 if is_admin else 0))
        conn.commit()
        return True, "계정이 생성되었습니다."


def deactivate_user(user_id):
    """사용자 비활성화 (effective_end_date = now)"""
    with get_db() as conn:
        conn.execute('''
            UPDATE isd_user SET effective_end_date = CURRENT_TIMESTAMP WHERE id = ?
        ''', (user_id,))
        conn.commit()
        return True, "계정이 비활성화되었습니다."


def get_all_users():
    """전체 사용자 목록 조회"""
    with get_db() as conn:
        rows = conn.execute('''
            SELECT * FROM isd_user ORDER BY created_at DESC
        ''').fetchall()
        return [dict(r) for r in rows]


def get_user_company_ids(user_id):
    """사용자에게 배정된 company_id 목록 반환"""
    with get_db() as conn:
        rows = conn.execute(
            'SELECT company_id FROM isd_user_company WHERE user_id = ?', (user_id,)
        ).fetchall()
        return {r['company_id'] for r in rows}


def set_user_companies(user_id, company_ids):
    """사용자의 회사 배정 목록을 교체 (기존 전체 삭제 후 재삽입)"""
    with get_db() as conn:
        conn.execute('DELETE FROM isd_user_company WHERE user_id = ?', (user_id,))
        for cid in company_ids:
            conn.execute(
                'INSERT OR IGNORE INTO isd_user_company (id, user_id, company_id) VALUES (?, ?, ?)',
                (str(uuid.uuid4()), user_id, cid)
            )
        conn.commit()


def update_user(user_id, user_name, user_email, is_admin):
    """사용자 정보 수정 (이름, 이메일, 관리자 여부)"""
    user_email = user_email.strip().lower()
    with get_db() as conn:
        existing = conn.execute(
            'SELECT id FROM isd_user WHERE user_email = ? AND id != ?', (user_email, user_id)
        ).fetchone()
        if existing:
            return False, "이미 사용 중인 이메일입니다."
        conn.execute('''
            UPDATE isd_user SET user_name = ?, user_email = ?, is_admin = ? WHERE id = ?
        ''', (user_name.strip(), user_email, 1 if is_admin else 0, user_id))
        conn.commit()
    return True, "계정 정보가 수정되었습니다."


def delete_user(user_id):
    """사용자 영구 삭제 (isd_user_company 포함 cascade)"""
    with get_db() as conn:
        conn.execute('DELETE FROM isd_user_company WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM isd_user WHERE id = ?', (user_id,))
        conn.commit()
    return True, "계정이 삭제되었습니다."


def can_access_company(company_id):
    """현재 로그인 사용자가 해당 company_id에 접근 가능한지 확인. Admin은 항상 True."""
    if session.get('is_admin'):
        return True
    user_id = session.get('user_id')
    if not user_id:
        return False
    return company_id in get_user_company_ids(user_id)
