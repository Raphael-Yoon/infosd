"""
infosd - 정보보호공시 관리 시스템
메인 Flask 애플리케이션
"""
import json
from flask import Flask, render_template, jsonify
from pathlib import Path
import os

_APP_DIR = Path(__file__).parent.resolve()
os.chdir(_APP_DIR)

# DB 마이그레이션 자동 실행 (앱 시작 시 미적용 마이그레이션 자동 반영)
from migrations.migration_manager import MigrationManager
_db_path = os.getenv('infosd_DB_PATH', str(_APP_DIR / 'infosd.db'))
MigrationManager(_db_path).upgrade()

from company_routes import bp_company
from disclosure_routes import bp_disclosure

app = Flask(__name__)
app.secret_key = os.getenv('infosd_SECRET_KEY', 'infosd-dev-secret-key-change-in-production')

app.config.update(
    TEMPLATES_AUTO_RELOAD=True,
    MAX_CONTENT_LENGTH=50 * 1024 * 1024,
)
app.jinja_env.auto_reload = True


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
