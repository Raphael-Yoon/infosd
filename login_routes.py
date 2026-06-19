"""
infosd 로그인 라우트
이메일 OTP 인증 기반 로그인/로그아웃
"""
import hmac
import hashlib
import time
import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from auth import (send_otp, verify_otp, admin_required, get_all_users,
                   create_user, deactivate_user, update_user, delete_user,
                   get_user_company_ids, set_user_companies)
from infosd_mail import send_gmail

_URL_PATTERN = re.compile(r'https?://|www\.', re.IGNORECASE)


def _validate_form_token(token, min_seconds=3):
    """폼 제출 토큰 검증 — 최소 min_seconds초 경과 여부 확인"""
    if not token:
        return False
    try:
        timestamp_str, sig = token.split('.', 1)
        secret = current_app.config.get('SECRET_KEY', current_app.secret_key)
        expected = hmac.new(secret.encode(), timestamp_str.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False
        return (int(time.time()) - int(timestamp_str)) >= min_seconds
    except (ValueError, AttributeError):
        return False


def _contains_url(text):
    return bool(_URL_PATTERN.search(text or ''))

bp_login = Blueprint('login', __name__)


def _is_local():
    """환경변수 기준 운영서버 여부를 확인하여 로컬 관리자 로그인 허용 여부 반환"""
    import os
    is_prod = (os.getenv('RUN_MODE') == 'prod') or \
              (os.getenv('FLASK_ENV') == 'production') or \
              (os.getenv('IS_PROD') == 'true')
    return not is_prod


@bp_login.route('/login', methods=['GET'])
def login_page():
    """로그인 화면"""
    if 'user_id' in session:
        return redirect(url_for('company.index'))
    return render_template('auth/login.html', show_local_login=_is_local())


@bp_login.route('/contact', methods=['GET', 'POST'])
def contact():
    """서비스 문의 페이지 (Contact Us)"""
    if request.method == 'POST':
        # Honeypot
        if request.form.get('website'):
            return render_template('auth/contact.html', success=True)

        # 폼 제출 시간 검증
        if not _validate_form_token(request.form.get('form_token')):
            return render_template('auth/contact.html',
                                   error='잘못된 요청입니다. 잠시 후 다시 시도해주세요.')

        name = request.form.get('name', '').strip()
        company_name = request.form.get('company_name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        if not all([name, email, message]):
            return render_template('auth/contact.html',
                                   error='이름, 이메일, 문의내용은 필수 입력 항목입니다.',
                                   name=name, company_name=company_name, email=email, message=message)

        if _contains_url(message):
            return render_template('auth/contact.html',
                                   error='문의 내용에 URL을 포함할 수 없습니다.',
                                   name=name, company_name=company_name, email=email, message=message)

        subject = f'[정보보호공시 시스템] 문의: {name}'
        body = f'이름: {name}\n소속/회사: {company_name}\n이메일: {email}\n\n문의내용:\n{message}'
        try:
            send_gmail(to='snowball1566@gmail.com', subject=subject, body=body)
            return render_template('auth/contact.html', success=True)
        except Exception as e:
            return render_template('auth/contact.html',
                                   error=f'전송 중 오류가 발생했습니다: {e}',
                                   name=name, company_name=company_name, email=email, message=message)

    return render_template('auth/contact.html')


@bp_login.route('/tour')
def tour():
    """비로그인 사용자용 기능 둘러보기 페이지"""
    return render_template('auth/tour.html')


@bp_login.route('/login/local', methods=['POST'])
def local_admin_login():
    """로컬 환경 전용 — 첫 번째 어드민 계정으로 즉시 로그인 (OTP 생략)"""
    if not _is_local():
        return "로컬 환경에서만 사용 가능합니다.", 403

    from auth import get_db
    with get_db() as conn:
        row = conn.execute('''
            SELECT * FROM isd_user
            WHERE is_admin = 1
              AND (effective_end_date IS NULL OR effective_end_date > CURRENT_TIMESTAMP)
            ORDER BY created_at ASC LIMIT 1
        ''').fetchone()

    if not row:
        return render_template('auth/login.html', show_local_login=True,
                               error="등록된 어드민 계정이 없습니다. 먼저 계정을 추가해 주세요.")

    user = dict(row)
    session['user_id'] = user['id']
    session['user_name'] = user['user_name']
    session['user_email'] = user['user_email']
    session['is_admin'] = True
    session.permanent = True
    return redirect(url_for('company.index'))


@bp_login.route('/login/request', methods=['POST'])
def request_otp():
    """이메일 OTP 발송 요청"""
    email = request.form.get('email', '').strip().lower()
    if not email:
        return render_template('auth/login.html', show_local_login=_is_local(),
                               error="이메일을 입력해 주세요.")

    success, message = send_otp(email)
    if not success:
        return render_template('auth/login.html', show_local_login=_is_local(),
                               error=message, email=email)

    return render_template('auth/verify.html', email=email)


@bp_login.route('/login/verify', methods=['POST'])
def verify_otp_view():
    """OTP 검증 및 세션 생성"""
    email = request.form.get('email', '').strip().lower()
    otp = request.form.get('otp', '').strip()

    success, result = verify_otp(email, otp)
    if not success:
        return render_template('auth/verify.html', email=email, error=result)

    user = result
    session['user_id'] = user['id']
    session['user_name'] = user['user_name']
    session['user_email'] = user['user_email']
    session['is_admin'] = bool(user['is_admin'])
    session.permanent = True

    return redirect(url_for('company.index'))


@bp_login.route('/logout', methods=['POST'])
def logout():
    """로그아웃"""
    session.clear()
    return redirect(url_for('login.login_page'))


# ─── 어드민: 계정 관리 ───────────────────────────

@bp_login.route('/admin/users', methods=['GET'])
@admin_required
def admin_users():
    """계정 관리 화면"""
    from db_config import get_db
    users = get_all_users()
    with get_db() as conn:
        raw_companies = conn.execute(
            'SELECT id, name FROM isd_companies ORDER BY name'
        ).fetchall()
        companies = []
        for c in raw_companies:
            targets = [dict(t) for t in conn.execute(
                'SELECT year FROM isd_targets WHERE company_id = ? ORDER BY year DESC',
                (c['id'],)
            ).fetchall()]
            companies.append({'id': c['id'], 'name': c['name'], 'targets': targets})
    user_companies = {u['id']: list(get_user_company_ids(u['id'])) for u in users}
    current_year = datetime.now().year
    return render_template('auth/admin_users.html', users=users,
                           companies=companies, user_companies=user_companies,
                           current_year=current_year)


@bp_login.route('/admin/users/add', methods=['POST'])
@admin_required
def admin_add_user():
    """사용자 추가"""
    user_name = request.form.get('user_name', '').strip()
    user_email = request.form.get('user_email', '').strip().lower()
    is_admin = request.form.get('is_admin') == 'on'

    current_year = datetime.now().year
    if not user_name or not user_email:
        users = get_all_users()
        from db_config import get_db
        with get_db() as conn:
            companies = [dict(r) for r in conn.execute(
                'SELECT id, name FROM isd_companies ORDER BY name'
            ).fetchall()]
        user_companies = {u['id']: list(get_user_company_ids(u['id'])) for u in users}
        return render_template('auth/admin_users.html', users=users,
                               companies=companies, user_companies=user_companies,
                               current_year=current_year, error="이름과 이메일을 모두 입력해 주세요.")

    success, message = create_user(user_name, user_email, is_admin)
    from db_config import get_db
    users = get_all_users()
    with get_db() as conn:
        companies = [dict(r) for r in conn.execute(
            'SELECT id, name FROM isd_companies ORDER BY name'
        ).fetchall()]
    user_companies = {u['id']: list(get_user_company_ids(u['id'])) for u in users}
    if success:
        return render_template('auth/admin_users.html', users=users,
                               companies=companies, user_companies=user_companies,
                               current_year=current_year, success=message)
    return render_template('auth/admin_users.html', users=users,
                           companies=companies, user_companies=user_companies,
                           current_year=current_year, error=message)


@bp_login.route('/admin/users/<user_id>/deactivate', methods=['POST'])
@admin_required
def admin_deactivate_user(user_id):
    """사용자 비활성화"""
    deactivate_user(user_id)
    return redirect(url_for('login.admin_users'))


@bp_login.route('/admin/users/<user_id>/edit', methods=['POST'])
@admin_required
def admin_edit_user(user_id):
    """사용자 정보 수정 (이름, 이메일, 관리자 여부)"""
    user_name = request.form.get('user_name', '').strip()
    user_email = request.form.get('user_email', '').strip().lower()
    is_admin = request.form.get('is_admin') == 'on'

    current_year = datetime.now().year
    from db_config import get_db
    users = get_all_users()
    with get_db() as conn:
        raw_companies = conn.execute('SELECT id, name FROM isd_companies ORDER BY name').fetchall()
        companies = []
        for c in raw_companies:
            targets = [dict(t) for t in conn.execute(
                'SELECT year FROM isd_targets WHERE company_id = ? ORDER BY year DESC', (c['id'],)
            ).fetchall()]
            companies.append({'id': c['id'], 'name': c['name'], 'targets': targets})
    user_companies = {u['id']: list(get_user_company_ids(u['id'])) for u in users}

    if not user_name or not user_email:
        return render_template('auth/admin_users.html', users=users, companies=companies,
                               user_companies=user_companies, current_year=current_year,
                               error="이름과 이메일을 모두 입력해 주세요.")

    success, message = update_user(user_id, user_name, user_email, is_admin)
    users = get_all_users()
    user_companies = {u['id']: list(get_user_company_ids(u['id'])) for u in users}
    if success:
        return render_template('auth/admin_users.html', users=users, companies=companies,
                               user_companies=user_companies, current_year=current_year,
                               success=message)
    return render_template('auth/admin_users.html', users=users, companies=companies,
                           user_companies=user_companies, current_year=current_year,
                           error=message)


@bp_login.route('/admin/users/<user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    """사용자 영구 삭제"""
    if user_id == session.get('user_id'):
        from db_config import get_db
        users = get_all_users()
        with get_db() as conn:
            raw_companies = conn.execute('SELECT id, name FROM isd_companies ORDER BY name').fetchall()
            companies = []
            for c in raw_companies:
                targets = [dict(t) for t in conn.execute(
                    'SELECT year FROM isd_targets WHERE company_id = ? ORDER BY year DESC', (c['id'],)
                ).fetchall()]
                companies.append({'id': c['id'], 'name': c['name'], 'targets': targets})
        user_companies = {u['id']: list(get_user_company_ids(u['id'])) for u in users}
        return render_template('auth/admin_users.html', users=users, companies=companies,
                               user_companies=user_companies, current_year=datetime.now().year,
                               error="본인 계정은 삭제할 수 없습니다.")

    delete_user(user_id)
    return redirect(url_for('login.admin_users'))


@bp_login.route('/admin/users/<user_id>/companies', methods=['POST'])
@admin_required
def admin_set_user_companies(user_id):
    """사용자-회사 배정 저장"""
    company_ids = [cid for cid in request.form.getlist('company_ids') if cid]
    set_user_companies(user_id, company_ids)
    from db_config import get_db
    users = get_all_users()
    with get_db() as conn:
        companies = [dict(r) for r in conn.execute(
            'SELECT id, name FROM isd_companies ORDER BY name'
        ).fetchall()]
    user_companies = {u['id']: list(get_user_company_ids(u['id'])) for u in users}
    return render_template('auth/admin_users.html', users=users,
                           companies=companies, user_companies=user_companies,
                           current_year=datetime.now().year,
                           success="회사 배정이 저장되었습니다.")


# ─── 어드민: 계정 전환 ───────────────────────────

@bp_login.route('/admin/switch_user', methods=['POST'])
@admin_required
def admin_switch_user():
    """관리자가 다른 사용자 계정으로 세션 전환"""
    target_user_id = request.form.get('target_user_id')
    if not target_user_id:
        return jsonify({'success': False, 'message': '대상 사용자를 지정해주세요.'})

    from db_config import get_db
    with get_db() as conn:
        row = conn.execute(
            'SELECT * FROM isd_user WHERE id = ? AND (effective_end_date IS NULL OR effective_end_date > CURRENT_TIMESTAMP)',
            (target_user_id,)
        ).fetchone()

    if not row:
        return jsonify({'success': False, 'message': '유효하지 않은 사용자입니다.'})

    user = dict(row)
    if 'original_admin_id' not in session:
        session['original_admin_id'] = session['user_id']
    session['user_id'] = user['id']
    session['user_name'] = user['user_name']
    session['user_email'] = user['user_email']
    session['is_admin'] = bool(user['is_admin'])

    return jsonify({'success': True, 'message': f"{user['user_name']} 계정으로 전환되었습니다."})


@bp_login.route('/admin/switch_back', methods=['GET'])
def admin_switch_back():
    """전환된 세션을 원래 관리자 계정으로 복귀"""
    original_id = session.get('original_admin_id')
    if not original_id:
        return redirect(url_for('company.index'))

    from db_config import get_db
    with get_db() as conn:
        row = conn.execute('SELECT * FROM isd_user WHERE id = ?', (original_id,)).fetchone()

    if not row:
        session.clear()
        return redirect(url_for('login.login_page'))

    user = dict(row)
    session['user_id'] = user['id']
    session['user_name'] = user['user_name']
    session['user_email'] = user['user_email']
    session['is_admin'] = True
    session.pop('original_admin_id', None)

    return redirect(url_for('company.index'))


@bp_login.route('/admin/api/users', methods=['GET'])
@admin_required
def admin_api_users():
    """계정 전환 모달용 — 활성 사용자 목록 반환"""
    from db_config import get_db
    current_id = session.get('user_id')
    with get_db() as conn:
        rows = conn.execute('''
            SELECT u.id, u.user_name, u.user_email, u.is_admin,
                   c.name as company_name
            FROM isd_user u
            LEFT JOIN isd_user_company uc ON u.id = uc.user_id
            LEFT JOIN isd_companies c ON uc.company_id = c.id
            WHERE (u.effective_end_date IS NULL OR u.effective_end_date > CURRENT_TIMESTAMP)
              AND u.id != ?
            ORDER BY u.is_admin ASC, u.user_name
        ''', (current_id,)).fetchall()
        users = [dict(r) for r in rows]

    return jsonify({'success': True, 'users': users})
