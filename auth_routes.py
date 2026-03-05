"""
infosd - 인증 라우팅 (로그인/로그아웃)
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from db_config import get_db

bp_auth = Blueprint('auth', __name__)


@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    """로그인 처리"""
    if 'user_id' in session:
        return redirect(url_for('company.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        with get_db() as conn:
            user = conn.execute(
                'SELECT id, password FROM ipd_users WHERE username = ? AND is_active = 1',
                (username,)
            ).fetchone()

            if user and check_password_hash(user['password'], password):
                conn.execute(
                    'UPDATE ipd_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                    (user['id'],)
                )
                conn.commit()
                session['user_id'] = user['id']
                session['username'] = username
                return redirect(url_for('company.index'))

        flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'error')

    return render_template('login.html')


@bp_auth.route('/logout', methods=['POST'])
def logout():
    """로그아웃"""
    session.clear()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('auth.login'))
