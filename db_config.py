"""
[개발3팀 InfoSD] 데이터베이스 설정 및 연결 관리 모듈
- 운영서버 (IS_PROD=true): MySQL 전용 DB 스페이스('infosd') 사용 (공시 데이터 무결성 및 ACID 보장)
- 개발환경 (IS_PROD=false): SQLite ('infosd.db') 사용 (로컬 개발 및 테스트 전용)
"""

import os
import sys
import uuid
import sqlite3
import urllib.parse
from decimal import Decimal
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Dict, Optional

_BASE_DIR = Path(__file__).resolve().parent
_WORKSPACE_DIR = _BASE_DIR.parent
DEFAULT_SQLITE_PATH = str(_BASE_DIR / 'infosd.db')

# .env 파일 자동 탐색 및 로드
try:
    from dotenv import load_dotenv
    for env_candidate in [_BASE_DIR / '.env', _WORKSPACE_DIR / '.env', _WORKSPACE_DIR / 'snowball' / '.env']:
        if env_candidate.exists():
            load_dotenv(env_candidate, override=False)
except Exception:
    pass

# 환경 판별: IS_PROD 환경변수 기준 (snowball/trade/cbt 표준)
# IS_PROD=true  -> 운영서버 (MySQL 'infosd' DB 전용)
# IS_PROD=false -> 개발환경 (SQLite 전용)
_is_prod_env = os.getenv("IS_PROD", "").strip().lower()
_db_type_env = os.getenv("INFOSD_DB_TYPE") or os.getenv("DB_TYPE", "")

if _db_type_env.lower() in ("mysql", "sqlite"):
    DB_TYPE = _db_type_env.lower()
elif _is_prod_env in ("true", "1", "yes"):
    DB_TYPE = "mysql"
elif _is_prod_env in ("false", "0", "no"):
    DB_TYPE = "sqlite"
else:
    # 기본값: .env 없는 기본 개발 환경에서는 자동으로 SQLite 사용
    DB_TYPE = "sqlite"

# MySQL 기본 접속 정보 (운영서버 전용 DB: infosd)
DEFAULT_MYSQL_URL = "mysql://root:150606@127.0.0.1:3306/infosd"
DATABASE_URL = os.getenv("INFOSD_DATABASE_URL") or os.getenv("DATABASE_URL") or DEFAULT_MYSQL_URL
SQLITE_DATABASE = os.getenv('infosd_DB_PATH', DEFAULT_SQLITE_PATH)


def _parse_mysql_url(url_str: str) -> Dict[str, Any]:
    parsed = urllib.parse.urlparse(url_str)
    
    # DB 스페이스 격리: INFOSD_DATABASE -> INFOSD_DATABASE_URL의 db명 -> 'infosd' 기본값
    infosd_db_name = os.getenv("INFOSD_DATABASE")
    if not infosd_db_name:
        if os.getenv("INFOSD_DATABASE_URL"):
            infosd_db_name = urllib.parse.urlparse(os.getenv("INFOSD_DATABASE_URL")).path.lstrip("/")
        else:
            infosd_db_name = "infosd"

    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": parsed.username or "root",
        "password": parsed.password or "150606",
        "database": infosd_db_name,
        "charset": "utf8mb4",
    }


def generate_uuid():
    """UUID v4 문자열 생성"""
    return str(uuid.uuid4())


class _DictRow(dict):
    """딕셔너리를 SQLite Row처럼 인덱스/키 접근 모두 지원하는 래퍼"""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class _AdaptedCursor:
    """sqlite3 ? 플레이스홀더를 pymysql %s로 자동 변환하는 커서 래퍼"""

    def __init__(self, cursor):
        self._cur = cursor

    @staticmethod
    def _adapt(query: str, has_params: bool):
        if has_params:
            # % 문자 이스케이프 및 ? -> %s 치환
            # 이미 %s 가 있는 경우는 건드리지 않고 ? 만 변환
            parts = query.split('?')
            adapted = '%s'.join(p.replace('%', '%%') for p in parts)
            # %%s -> %s 복원
            adapted = adapted.replace('%%s', '%s')
            return adapted
        return query

    def execute(self, query: str, params=None):
        if query.strip().upper().startswith('PRAGMA'):
            return self
        adapted = self._adapt(query, params is not None)
        if params is not None:
            if not isinstance(params, (tuple, list, dict)):
                params = (params,)
            self._cur.execute(adapted, params)
        else:
            self._cur.execute(adapted)
        return self

    def executemany(self, query: str, seq_of_params):
        adapted = self._adapt(query, True)
        self._cur.executemany(adapted, seq_of_params)
        return self

    @staticmethod
    def _conv_row(row):
        if not row:
            return None
        return _DictRow({
            k: float(v) if isinstance(v, Decimal) else (str(v) if hasattr(v, 'strftime') else v)
            for k, v in row.items()
        })

    def fetchone(self):
        row = self._cur.fetchone()
        return self._conv_row(row) if row else None

    def fetchall(self):
        rows = self._cur.fetchall()
        return [self._conv_row(r) for r in rows] if rows else []

    @property
    def rowcount(self):
        return self._cur.rowcount

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    @property
    def description(self):
        return self._cur.description

    def close(self):
        try:
            self._cur.close()
        except Exception:
            pass


class _PyMySQLAdapter:
    """sqlite3 Connection 인터페이스를 지원하는 PyMySQL 래퍼"""

    def __init__(self, config: Dict[str, Any]):
        import pymysql
        import pymysql.cursors

        self._config = config
        self._conn = pymysql.connect(
            **config,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
            connect_timeout=10,
        )

    @property
    def row_factory(self):
        return None

    @row_factory.setter
    def row_factory(self, value):
        pass

    def cursor(self):
        return _AdaptedCursor(self._conn.cursor())

    def execute(self, query: str, params=None):
        if query.strip().upper().startswith('PRAGMA'):
            return _AdaptedCursor(self._conn.cursor())
        cur = self.cursor()
        cur.execute(query, params)
        return cur

    def executemany(self, query: str, seq_of_params):
        cur = self.cursor()
        cur.executemany(query, seq_of_params)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()


def init_db():
    """MySQL 전용 DB 및 12개 테이블 초기화"""
    if DB_TYPE == "mysql":
        import pymysql

        config = _parse_mysql_url(DATABASE_URL)
        db_name = config["database"]

        # 1) infosd 데이터베이스 생성
        server_config = config.copy()
        server_config.pop("database", None)
        conn = pymysql.connect(**server_config, autocommit=True)
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.close()

        # 2) infosd 테이블 DDL 생성
        conn = pymysql.connect(**config, autocommit=True)
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS isd_companies (
                    id VARCHAR(100) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS isd_targets (
                    id VARCHAR(100) PRIMARY KEY,
                    company_id VARCHAR(100) NOT NULL,
                    year INT NOT NULL,
                    status VARCHAR(50) DEFAULT 'draft',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_company_year (company_id, year)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS isd_questions (
                    id VARCHAR(100) PRIMARY KEY,
                    display_number VARCHAR(50),
                    level INT NOT NULL,
                    category_id INT NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    subcategory VARCHAR(100),
                    text TEXT NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    options TEXT,
                    parent_question_id VARCHAR(100),
                    dependent_question_ids TEXT,
                    required INT DEFAULT 1,
                    help_text TEXT,
                    evidence_list TEXT,
                    sort_order INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    evidence_title TEXT,
                    is_active INT DEFAULT 1
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS isd_answers (
                    id VARCHAR(100) PRIMARY KEY,
                    question_id VARCHAR(100) NOT NULL,
                    company_id VARCHAR(100) NOT NULL,
                    year INT NOT NULL,
                    value MEDIUMTEXT,
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    deleted_at DATETIME NULL,
                    UNIQUE KEY uq_q_comp_year (question_id, company_id, year)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS isd_evidence (
                    id VARCHAR(100) PRIMARY KEY,
                    answer_id VARCHAR(100),
                    question_id VARCHAR(100),
                    company_id VARCHAR(100) NOT NULL,
                    year INT NOT NULL,
                    file_name VARCHAR(255) NOT NULL,
                    file_url VARCHAR(500) NOT NULL,
                    file_size INT,
                    file_type VARCHAR(50),
                    evidence_type VARCHAR(100),
                    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS isd_sessions (
                    id VARCHAR(100) PRIMARY KEY,
                    company_id VARCHAR(100) NOT NULL,
                    year INT NOT NULL,
                    status VARCHAR(50) DEFAULT 'draft',
                    total_questions INT DEFAULT 0,
                    answered_questions INT DEFAULT 0,
                    completion_rate INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    submitted_at DATETIME NULL,
                    UNIQUE KEY uq_sess_comp_year (company_id, year)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS isd_submissions (
                    id VARCHAR(100) PRIMARY KEY,
                    session_id VARCHAR(100) NOT NULL,
                    company_id VARCHAR(100) NOT NULL,
                    year INT NOT NULL,
                    submission_data MEDIUMTEXT,
                    submission_details MEDIUMTEXT,
                    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    confirmation_number VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'draft'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS isd_answer_history (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    company_id VARCHAR(100) NOT NULL,
                    year INT NOT NULL,
                    question_id VARCHAR(100) NOT NULL,
                    old_value MEDIUMTEXT,
                    new_value MEDIUMTEXT,
                    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    changed_by VARCHAR(100) DEFAULT 'system',
                    INDEX idx_comp_year (company_id, year)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ipd_users (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    is_active INT DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS isd_user (
                    id VARCHAR(100) PRIMARY KEY,
                    user_name VARCHAR(100) NOT NULL,
                    user_email VARCHAR(255) NOT NULL UNIQUE,
                    is_admin INT NOT NULL DEFAULT 0,
                    otp_code VARCHAR(50),
                    otp_expires_at DATETIME NULL,
                    otp_attempts INT NOT NULL DEFAULT 0,
                    effective_start_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    effective_end_date DATETIME NULL,
                    last_login_at DATETIME NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS isd_user_company (
                    id VARCHAR(100) PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    company_id VARCHAR(100) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_user_company (user_id, company_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS isd_migration_history (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    version VARCHAR(100) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    execution_time_ms INT,
                    status VARCHAR(50) DEFAULT 'success'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
        conn.close()
        print(f"[InfoSD DB] [운영서버 모드] MySQL '{db_name}' 데이터베이스 및 12개 테이블 준비 완료.")
        return


def get_db_connection():
    """환경에 따른 DB 연결 객체 반환"""
    if DB_TYPE == "mysql":
        config = _parse_mysql_url(DATABASE_URL)
        return _PyMySQLAdapter(config)
    else:
        conn = sqlite3.connect(SQLITE_DATABASE)
        conn.row_factory = sqlite3.Row
        return conn


@contextmanager
def get_db():
    """컨텍스트 매니저로 데이터베이스 연결 제공 (커밋/롤백/자동 닫기)"""
    conn = get_db_connection()
    try:
        yield conn
        if DB_TYPE != "mysql":
            conn.commit()
    except Exception:
        if DB_TYPE != "mysql":
            conn.rollback()
        raise
    finally:
        conn.close()
