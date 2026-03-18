# infosd 작업 로그

---

## 2026-03-18 (v1.15)

### 변경 내역
- [테스트] `test/test_unit_infosd.py`: 37개 유닛 테스트 전면 재작성 및 100% 통과 달성
  - `PlaywrightTestBase._api()` 추가: 브라우저 쿠키 추출 후 `requests` HTTP 호출 (인증 유지)
  - `_login()` 추가: `/login/local` OTP-없는 로컬 어드민 로그인
  - `_ensure_session()` 재작성: 매 호출 시 `/disclosure/select/{id}/{year}` 네비게이션으로 Flask session 강제 갱신
  - 회사·연도 관리 테스트 6개: 가상 REST API → 실제 form POST 엔드포인트로 교체
  - `test_validation_b_gt_a`: Q4/Q5/Q6 초기화 후 Q2 저장 (이전 테스트 데이터 간섭 방지)
  - `test_validation_personnel`: Q28 초기화 후 Q10 저장 (동일 이유)
  - `test_evidence_section_toggle_by_value`: `dispatch_event("input")` → `dispatch_event("change")`
  - 신규 테스트 4개 추가: none_hidden(Q29), checkbox(Q20), confirmed 잠금, evidence 섹션 토글
- [테스트] `test/unit_checklist_infosd.md`: 시나리오 13~15 추가 (none_hidden, checkbox, confirmed 잠금)
- [버그] `disclosure_routes.py`: `save_answer` table 빈 행 필터 — `해당없음='Y'` 행 보존
  - 기존: 모든 필드가 비어있는 행 제거 → `해당없음=Y` 행도 제거되어 `[]` 저장
  - 수정: `row.get('해당없음') == 'Y'` 행은 무조건 보존
  - 영향: `_get_none_hidden_ids` Q29 none_hidden 처리 정상화
- [버그] `disclosure_routes.py`: `save_answer` checkbox 타입 `str.items()` 오류 수정
  - 기존: `isinstance(value, list)` 후 모든 요소에 `.items()` 호출 → checkbox(문자열 배열)에서 500
  - 수정: `isinstance(value[0], dict)` 체크 추가 — table 타입만 빈 행 필터링 적용
- [버그] `disclosure_routes.py`: `_mark_dependents_na` / `_clear_na_from_dependents` 미작동 수정
  - 원인: `dependent_question_ids` 필드가 DB 전체에서 NULL — 함수가 사실상 NOP이었음
  - 수정: `parent_question_id` 역방향 조회 방식으로 `_get_all_dependent_ids` 전면 재설계
  - 영향: Q1=NO 시 Q2 등 하위 질문 자동 N/A 처리 정상화
- [테스트] `test/playwright_base.py`: `_api()` 헬퍼 메서드 추가

### 변경 파일
- `disclosure_routes.py`: `_get_all_dependent_ids` 역방향 조회 재설계, `_mark_dependents_na` / `_clear_na_from_dependents` 단순화, `save_answer` 빈 행 필터·checkbox 타입 버그 2건 수정
- `test/playwright_base.py`: `_api()` 메서드 추가
- `test/test_unit_infosd.py`: 전면 재작성 (37개 테스트 100% 통과)
- `test/unit_checklist_infosd.md`: 시나리오 13~15 추가
- `test/unit_checklist_infosd_result.md`: 최신 테스트 결과 갱신

---

## 2026-03-18 (v1.14)

### 변경 내역
- [버그] `disclosure_routes.py`: `dashboard()` overall 이중 계산 버그 수정
  - cat_list에 증빙 반영 후 `_calc_evidence_progress` 재호출로 분모 과다 산정되던 문제 제거
  - `overall = int((total_done / total_q) * 100)` 단일 공식으로 통일
- [버그] `disclosure_routes.py`: `cert_count` 계산 기준 수정
  - 기존: Q16 답변 존재 여부(0 or 1)
  - 변경: Q16 테이블 JSON 파싱 후 실제 행 수 집계 (Q15=YES 조건 유지)
- [버그] `disclosure_routes.py`: `history_view()`, `serve_evidence()` 테이블명 수정
  - `ipd_companies` → `isd_companies`
  - `ipd_answer_history` → `isd_answer_history`
  - `ipd_questions` → `isd_questions`
  - `ipd_evidence` → `isd_evidence`
- [UI] `templates/disclosure/dashboard.html`: "완료: X/Y (답변 + 증빙)" 텍스트 통일
- [UI] `templates/disclosure/dashboard.html`, `work.html`: 메뉴명 "최종 검토"로 통일
  - "전체 작성 내용 검토" → "최종 검토"
  - "최종 리뷰" → "최종 검토"
- [운영] `CLAUDE.md`: 팀 운영 규칙 업데이트
  - '샘' 호칭 전면 제거, 군 계급 기반 호칭 체계 명문화
  - 위계질서 반영: 정래훈(선임 병장) > 이태욱(병장) > 양필조·임태준(상병) > 김종규(일병)
  - 계급별 말투 규칙 테이블 추가

### 변경 파일
- `disclosure_routes.py`: overall 이중계산 버그 수정, cert_count Q16 행 수 기준으로 수정, ipd_ → isd_ 테이블명 4곳 수정
- `templates/disclosure/dashboard.html`: 진행률 텍스트 수정, "최종 검토" 텍스트 통일
- `templates/disclosure/work.html`: "최종 검토" 텍스트 통일
- `CLAUDE.md`: 호칭 체계 및 위계질서 전면 업데이트

---

## 2026-03-17 (v1.13)

### 변경 내역
- [기능] 작업 페이지 카테고리별 진행률(%)에 증빙 업로드 반영
  - `work()` 뷰: `_calc_cat_progress` 호출 후 카테고리별 증빙 필수 항목 수/완료 수를 계산하여 `cat.rate` 재산정
  - 증빙 필요 항목이 있는 카테고리는 모든 증빙 업로드 전까지 100% 미표시

### 변경 파일
- `disclosure_routes.py`: `work()` 뷰 내 카테고리별 증빙 진행률 계산 로직 추가

---

## 2026-03-17 (v1.12)

### 변경 내역
- [기능] 공시 확정 흐름 단순화: 검토 요청(submit) 단계 제거, draft → confirmed 직접 확정 가능
  - `disclosure_routes.py`: `confirm_disclosure` 조건을 `status != 'submitted'` → `status == 'confirmed'` 로 변경 (draft/submitted 모두 확정 허용)
  - `review.html`: submitted 브랜치 제거, else(draft)에서 바로 `/disclosure/confirm` 폼 노출
  - `dashboard.html`: submitted 브랜치 제거, `overall == 100` 버튼 "검토 요청하기" → "확정하기"
- [UI] dashboard.html: submitted 상태 주황 배너 및 뱃지 제거, 100% 완료 뱃지 "작성 완료 (검토 요청 대기)" → "작성 완료"
- [기능] 진행률 계산에 증빙 업로드 반영: 답변 완료만으로 100% 달성 불가, 필수 증빙 업로드 완료 시 100%
  - `_calc_evidence_progress()` 헬퍼 함수 추가
  - `_update_session_progress()`: DB `completion_rate` 계산에 증빙 반영
  - `dashboard()`, `review()` view: `overall` 계산에 증빙 반영
- [UI] review.html: 미작성/증빙미업로드 항목 시각 강조
  - 행 테두리: 미작성 → 빨간색, 증빙 필요 → 주황색, 완료 → 초록색
  - 증빙 셀: 미업로드 시 "증빙 필요" 경고 배지 (노란 고정색, 다크모드 호환)
  - 미입력 항목은 증빙 배지 미표시 (답변 완료 후에만 표시)
- [UX] review.html: 미작성/증빙필요 클릭 시 작업 페이지로 이동
  - "미작성" 클릭 → `/disclosure/work?category=X#card-Q번호`
  - "증빙 필요" 클릭 → `/disclosure/work?category=X#ev-section-Q번호`

### 변경 파일
- `disclosure_routes.py`: `_calc_evidence_progress()` 추가, `confirm_disclosure` 조건 완화, 진행률 3곳 수정
- `templates/disclosure/dashboard.html`: submitted 흐름 제거, 뱃지·버튼 문구 수정
- `templates/disclosure/review.html`: 확정 버튼 단순화, 행 색상·증빙 배지·클릭 링크 추가

---

## 2026-03-17 (v1.11)

### 변경 내역
- [기능] login_routes.py: 계정 수정(`/admin/users/<id>/edit`) 및 영구 삭제(`/admin/users/<id>/delete`) 라우트 추가
  - `admin_edit_user`: 이름·이메일·관리자 권한 수정. 이메일 중복 시 오류 반환
  - `admin_delete_user`: 영구 삭제 (isd_user_company cascade). 본인 계정 삭제 서버 레벨 차단
- [기능] auth.py: `update_user()`, `delete_user()` 함수 추가
- [UI] admin_users.html: 계정 관리 열에 편집(✏️) 및 삭제(🗑️) 버튼 추가
  - 편집: per-user 모달 (이름·이메일·관리자권한 pre-fill)
  - 삭제: confirm 다이얼로그 + 본인 계정 버튼 미출력 (템플릿 레벨 차단)
- [테스트] test_unit_infosd.py: `test_answer_confirmed_blocked` SKIP 해소
  - DB 직접 주입 방식으로 자동화: sqlite3로 isd_sessions.status='confirmed' 강제 설정 후 403 검증, finally에서 원상복구

### 변경 파일
- `auth.py`: `update_user()`, `delete_user()` 함수 추가
- `login_routes.py`: import 수정, `admin_edit_user` / `admin_delete_user` 라우트 추가
- `templates/auth/admin_users.html`: 편집 버튼·모달, 삭제 버튼 추가
- `test/test_unit_infosd.py`: `test_answer_confirmed_blocked` DB 직접 주입 방식으로 재구현

---

## 2026-03-17

### 변경 내역
- [UI] dashboard.html: 버튼 문구 "기업 목록으로" → "홈으로" 수정 (아이콘·의미 일치 및 단일 기업 사용자 UX 개선)

### 변경 파일
- `templates/disclosure/dashboard.html`: 홈 버튼 문구 통일

---

## 2026-03-16

### 변경 내역
- [기능] login_routes.py: 관리자 계정 전환 기능 구현 (Snowball 동일 방식 포팅)
  - `POST /admin/switch_user` — 관리자가 다른 사용자 세션으로 전환 (original_admin_id 세션 백업)
  - `GET /admin/switch_back` — 원래 관리자 계정으로 복귀
  - `GET /admin/api/users` — 계정 전환 모달용 활성 사용자 목록 API (본인 제외)
- [기능] login_routes.py: 이전 세션 버그 수정 (v1.08 관련 누적 수정)
  - admin_add_user / admin_set_user_companies 라우트에 current_year 누락 수정
  - company_ids 필터링: 빈 문자열 제거 (라디오 "없음" 옵션 처리)
- [UI] templates/base.html: 네비바 계정 전환 UI 추가
  - Admin 상태: 이름 클릭 시 계정 전환 모달 오픈 (fa-user-secret 아이콘)
  - 전환 중: "관리자로 돌아가기" 버튼(노란색) 표시, 관리자 메뉴 숨김
  - switchToUser() / showUserSwitchModal() JS 함수 전역 등록
- [UI] templates/auth/admin_users.html: 계정 목록 각 행에 전환 버튼 추가 (활성 계정, 본인 제외)
- [버그] templates/auth/admin_users.html: set() → [] Jinja2 호환 수정
- [UI] templates/auth/admin_users.html: 회사 배정 모달 체크박스 → 라디오버튼 (계정당 회사 1개 정책 반영), 전체 행 클릭 가능

### 변경 파일
- `login_routes.py`: 계정 전환 라우트 3개 추가, current_year 누락 수정, company_ids 필터 추가
- `templates/base.html`: 네비바 계정 전환 UI 및 JS 추가, 플로팅 매뉴얼 버튼 위치 조정
- `templates/auth/admin_users.html`: 전환 버튼 추가, set()→[] 수정, 라디오버튼 방식 회사 배정 모달

---

## 2026-03-12

### 변경 내역
- [UI] work.html: 정보보호부문 투자액(B) Q4/Q5/Q6 inv-card에 증빙 업로드 섹션 추가
- [UI] work.html: number 타입 금액 0원 시 증빙 섹션 자동 숨김 — `toggleEvidenceByValue()` JS 함수 구현
- [UI] work.html: 입력 필드 배경색 흰색 버그 수정 (`background: var(--bg-main)` 명시, Chromium autofill 대응)
- [UI] work.html: I-2 display_number 뱃지를 inv-grid-title에 추가
- [UI] work.html: 인력 항목(Q10/Q28/Q11/Q12) 컴팩트 2×2 그리드로 통합 렌더링
- [UI] work.html: I-3 투자비율(B/A), II-4 인력비율(D/C) ratio-bar 자동계산 표시 추가
- [UI] work.html: table 타입 "+ 행 추가" 버튼 onclick → data-cols + JSON.parse 방식으로 수정 (이중 따옴표 충돌 버그 수정)
- [UI] work.html: table 타입 증빙 섹션 항상 표시 (number 타입만 0원 조건 적용)
- [UI] index.html: 기업 삭제 시 확인 메시지 문구 강화 (복구 불가 안내 추가)
- [작가팀/UI] infosd 전체 질문 문구 및 도움말 개선 (작가팀 최종 검토 반영)
- [UI] dashboard.html/review.html: UI 디자인 미세 조정 및 레이아웃 최적화
- [백엔드] disclosure_routes.py: confirm 시 number 타입 0원 항목 필수 증빙 검증 제외 로직 추가
- [DB] Migration 011: display_number 전체 재정렬 — 정보보호공시 서식과 1:1 매핑 (I, I-1, I-2-가 … II-6 등)
- [DB] Migration 012: Q10(총 임직원) evidence_list 수정 — IT 인력 현황표/조직도 → 4대보험 가입자 명부/간이세액징수 신고서
- [DB] Migration 013: Q29(CISO/CPO 활동내역) evidence_list 추가 — CISO/CPO 활동 근거 서류 (회의록, 보고자료 등)
- [테스트] test_unit_infosd.py: 신규 7개 테스트 케이스 추가 (26개 → 33개)
  - table 타입 JSON 배열 저장 검증 (Q27)
  - 카테고리 1 투자 inv-grid + I-3 ratio-bar DOM 렌더링
  - 카테고리 2 인력 컴팩트 그리드 + II-4 ratio-bar DOM 렌더링
  - 투자비율/인력비율 자동계산 JS 표시 확인
  - table 타입 Q29 증빙 PDF 업로드·삭제
  - number 타입 금액 기반 증빙 섹션 토글
- [테스트] unit_checklist_infosd.md: 섹션 8~12 추가 (7개 시나리오)

### 변경 파일
- `templates/disclosure/work.html`: UI 개선 다수 (투자·인력 그리드, ratio-bar, 증빙 토글, 버그 수정)
- `templates/index.html`: 기업 삭제 확인 메시지 수정
- `disclosure_routes.py`: confirm 증빙 검증 로직 보완
- `migrations/versions/011_display_number_realign.py`: display_number 재정렬 마이그레이션 (신규)
- `migrations/versions/014_writer_team_final_review.py`: 작가팀 문구 개선 마이그레이션 (신규)
- `migrations/versions/012_fix_q10_evidence_list.py`: Q10 evidence_list 수정 마이그레이션 (신규)
- `migrations/versions/013_q29_evidence_list.py`: Q29 evidence_list 추가 마이그레이션 (신규)
- `test/test_unit_infosd.py`: 신규 테스트 케이스 7개 추가
- `test/unit_checklist_infosd.md`: 테스트 시나리오 섹션 8~12 추가

---

## 2026-03-05

### 변경 내역
- [DB] Migration 009: IT 감사팀 QA 점검 결과 반영 — 질문 완전성 보완 8건
  - Q13 문구: '지정 현황' → '지정 여부'
  - Q14 CISO/CPO 테이블: 임명일(appointed_date) 컬럼 추가
  - Q19 교육 실적 테이블: 실시일자(edu_date), 실시횟수(count) 컬럼 추가
  - Q20: yes_no → checkbox (지침서/절차서 개별 확인)
  - Q23 SBOM: number → select (4단계 현황 선택)
  - Q24 C-TAS: help_text 상호배타 안내 추가
  - Q27 주요투자 항목: textarea → table (항목명+금액+비고)
  - Q29 CISO 활동 내역: textarea → table (활동유형+내역+횟수)
- [DB] Migration 010: 작가팀 문구 검토 결과 반영 — 질문 표현 통일 5건
  - Q7 어조 통일: '있으신가요?' → '있나요?'
  - Q9 후행 공백 제거
  - Q13 질문형 전환: '지정 여부' → '지정되어 있나요?'
  - Q26 어법 오류 수정: '준비금 가입' → '배상 준비금을 적립하고 있나요?'
  - Q26 help_text 용어 통일: '적립금' → '배상 준비금'
- [설정] infosd.py: auth_routes 블루프린트 및 require_login 미들웨어 제거 (개발 편의)
- [테스트] test_unit_infosd.py: 전체 26개 시나리오 자동화 테스트 구현
- [테스트] unit_checklist_infosd_result.md: 테스트 결과 체크리스트 생성

### 변경 파일
- `migrations/versions/009_audit_qa_improvements.py`: IT 감사팀 QA 반영 마이그레이션 (신규)
- `migrations/versions/010_writer_qa_wording_fix.py`: 작가팀 문구 수정 마이그레이션 (신규)
- `infosd.py`: auth_routes 제거, 불필요 import 정리
- `infosd.db`: 마이그레이션 009·010 적용
- `test/test_unit_infosd.py`: 26개 유닛 테스트 시나리오 구현
- `test/unit_checklist_infosd_result.md`: 테스트 결과 리포트 (신규)

---

## 2026-03-04

### 변경 내역
- [UI] CISO/CPO 상세 현황(Q2-2-1) `table` 타입 입력 UI 구현 — 고정 2행(CISO/CPO), 6개 컬럼
- [UI] 인증 보유 현황(Q3-1-1) `table` 타입 동적 행 추가/삭제 UI 구현
- [UI] `checkbox` 타입 렌더링 신규 구현 (복수 선택, JSON 배열 저장)
- [DB] Q4 계열 전체 options 일괄 설정 (Q4-1-1, Q4-1-2, Q4-1-4, Q4-1-5, Q4-1-7, Q4-1-8)
- [DB] 전체 질문 `evidence_list` 일괄 설정 (15개 항목 — 투자액, 인력, 인증, 교육, 지침, 취약점, 훈련, 보험)
- [UI] 작업 화면 상단 네비게이션 바 제거 (하단 footer로 통합)
- [DB] Q27(주요 투자 항목) sort_order 수정: 28 → 7 (Q1-2 이전 정렬 위치 조정)
- [버그] `_is_question_active()` group 타입 부모 처리 순서 버그 수정 → 진행률 100% 정상화
- [버그] sidebar 진행률 계산 SQL → Python 로직으로 교체 (status 컬럼 의존성 제거)
- [UI] 투자액 합계 단위 KRW → 원 변경
- [DB] 2025년 테스트 투자액 데이터 현실화 (Q2: 5억, Q4: 5천만, Q5: 3천만, Q6: 2천만)
- [설정] CLAUDE.md 팀원 배경·경력 상세 추가, 사용자 존댓말 규칙 명시
- [설정] 작업 로그 관리 지침 추가 (CLAUDE.md 섹션 7)

### 변경 파일
- `templates/disclosure/work.html`: table/checkbox 타입 렌더링, nav 바 제거, 단위 수정
- `disclosure_routes.py`: `_is_question_active()` 버그 수정, sidebar 진행률 로직 교체
- `infosd.db`: Q4 options, evidence_list, sort_order, 테스트 데이터 업데이트
- `CLAUDE.md`: 팀원 배경 추가, 작업 로그 지침 추가
- `WORK_LOG.md`: 신규 생성
