"""
infosd - 정보보호공시 관리 시스템
메인 Flask 애플리케이션
"""
import hmac
import hashlib
import time
import json
from markupsafe import Markup
from flask import Flask, render_template, jsonify
from pathlib import Path
import os
from dotenv import load_dotenv

_APP_DIR = Path(__file__).parent.resolve()
os.chdir(_APP_DIR)
load_dotenv(_APP_DIR / '.env')

# DB 마이그레이션 자동 실행 (앱 시작 시 미적용 마이그레이션 자동 반영)
from migrations.migration_manager import MigrationManager
_db_path = os.getenv('infosd_DB_PATH', str(_APP_DIR / 'infosd.db'))
MigrationManager(_db_path).upgrade()

from datetime import timedelta
from company_routes import bp_company
from disclosure_routes import bp_disclosure
from login_routes import bp_login
from checker_routes import bp_checker

app = Flask(__name__)
app.secret_key = os.getenv('infosd_SECRET_KEY', 'infosd-dev-secret-key-change-in-production')

app.config.update(
    TEMPLATES_AUTO_RELOAD=True,
    MAX_CONTENT_LENGTH=50 * 1024 * 1024,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)
app.jinja_env.auto_reload = True


@app.context_processor
def inject_globals():
    """모든 템플릿에 form_token 전역 주입"""
    timestamp = str(int(time.time()))
    sig = hmac.new(app.secret_key.encode(), timestamp.encode(), hashlib.sha256).hexdigest()
    return {'form_token': f"{timestamp}.{sig}"}


# ─── Jinja2 커스텀 필터 ───────────────────────────
@app.template_filter('from_json_or_default')
def from_json_or_default(value, default=None):
    """JSON 문자열을 파싱. 실패 시 default 반환."""
    if default is None:
        default = []
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


@app.template_filter('format_audit_value')
def format_audit_value(value):
    """감사 로그 값(old_value/new_value)을 읽기 쉬운 HTML로 포맷.
    JSON 배열(인증 목록 등)은 항목별 요약 텍스트로, 단순 문자열은 그대로 반환."""
    if not value:
        return Markup('<span class="text-muted fst-italic">없음</span>')
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            if not parsed:
                return Markup('<span class="text-muted fst-italic">없음</span>')
            lines = []
            for item in parsed:
                if isinstance(item, dict):
                    parts = []
                    if 'cert_type' in item:
                        parts.append(f'<strong>{item["cert_type"]}</strong>')
                    vf = item.get('valid_from', '')
                    vt = item.get('valid_to', '')
                    if vf and vt:
                        parts.append(f'{vf} ~ {vt}')
                    num = item.get('cert_number', '')
                    if num:
                        parts.append(f'No.{num}')
                    lines.append(' | '.join(parts) if parts else ', '.join(f'{k}: {v}' for k, v in item.items()))
                else:
                    lines.append(str(item))
            return Markup('<br>'.join(lines))
        elif isinstance(parsed, dict):
            parts = [f'<span class="text-muted small">{k}:</span> {v}' for k, v in parsed.items()]
            return Markup('<br>'.join(parts))
        else:
            return str(parsed)
    except (json.JSONDecodeError, TypeError):
        return value


@app.template_filter('comma')
def comma_filter(value):
    """숫자에 쉼표(,) 추가 (천 단위)"""
    if value == '' or value is None:
        return ''
    try:
        clean_value = str(value).replace(',', '')
        if '.' in clean_value:
            return "{:,.2f}".format(float(clean_value)).rstrip('0').rstrip('.')
        return "{:,}".format(int(clean_value))
    except (ValueError, TypeError):
        return value


# Blueprint 등록
app.register_blueprint(bp_company)
app.register_blueprint(bp_disclosure)
app.register_blueprint(bp_login)
app.register_blueprint(bp_checker)


@app.route('/health')
def health():
    """서버 상태 확인"""
    return jsonify({'status': 'ok', 'service': 'infosd'})


@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, message='페이지를 찾을 수 없습니다.'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', code=500, message='서버 오류가 발생했습니다.'), 500


if __name__ == '__main__':
    port = int(os.getenv('infosd_PORT', 5001))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    print(f"\n infosd 서버 시작 — http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
