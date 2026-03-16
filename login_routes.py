"""
infosd 로그인 라우트
이메일 OTP 인증 기반 로그인/로그아웃
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session
from auth import (send_otp, verify_otp, admin_required, get_all_users,
                   create_user, deactivate_user, get_user_company_ids, set_user_companies)

bp_login = Blueprint('login', __name__)


def _is_local():
    """로컬호스트 접근 여부 확인"""
    return request.remote_addr in ('127.0.0.1', '::1')


@bp_login.route('/login', methods=['GET'])
def login_page():
    """로그인 화면"""
    if 'user_id' in session:
        return redirect(url_for('company.index'))
    return render_template('auth/login.html', show_local_login=_is_local())


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

    if not user_name or not user_email:
        users = get_all_users()
        return render_template('auth/admin_users.html', users=users, error="이름과 이메일을 모두 입력해 주세요.")

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
                               companies=companies, user_companies=user_companies, success=message)
    return render_template('auth/admin_users.html', users=users,
                           companies=companies, user_companies=user_companies, error=message)


@bp_login.route('/admin/users/<user_id>/deactivate', methods=['POST'])
@admin_required
def admin_deactivate_user(user_id):
    """사용자 비활성화"""
    deactivate_user(user_id)
    return redirect(url_for('login.admin_users'))


@bp_login.route('/admin/users/<user_id>/companies', methods=['POST'])
@admin_required
def admin_set_user_companies(user_id):
    """사용자-회사 배정 저장"""
    company_ids = request.form.getlist('company_ids')
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
                           success="회사 배정이 저장되었습니다.")
