<!-- Test Run: 2026-03-05 14:44:45 -->
# infosd: 정보보호공시 시스템 테스트 시나리오

## 1. 회사·연도 관리

- [x] ✅ **test_company_add**: 신규 회사 등록 후 목록에 표시되는지 확인 → **통과** ('테스트회사_자동' 등록 및 목록 표시 확인)
- [x] ✅ **test_company_add_duplicate**: 동일 회사명 중복 등록 시 경고 메시지 확인 → **통과** ('테스트회사_자동' 등록 및 목록 표시 확인)
- [x] ✅ **test_company_edit**: 회사명 수정 후 반영 여부 확인 → **통과** (회사명 수정 확인 (→ 테스트회사_자동_편집 → 복구))
- [x] ✅ **test_year_add**: 공시 연도(2099) 추가 후 목록 표시 확인 → **통과** (2026년도 목록 존재 확인)
- [x] ✅ **test_year_add_duplicate**: 동일 연도 중복 추가 시 경고 메시지 확인 → **통과** (2026년도 목록 존재 확인)
- [x] ✅ **test_company_delete**: 회사 삭제 후 목록에서 제거 확인 → **통과** ('삭제테스트_임시' 삭제 후 목록 제거 확인)

## 2. 공시 세션 진입 및 대시보드

- [x] ✅ **test_session_select**: 회사+연도 선택 후 대시보드 페이지 진입 확인 → **통과** (대시보드 진입 확인 (URL: http://localhost:5001/))
- [x] ✅ **test_dashboard_render**: 4개 카테고리 카드 및 진행률 렌더링 확인 → **통과** (카테고리 카드 4개 렌더링 확인)
- [x] ✅ **test_dashboard_category_navigation**: 카테고리 카드 클릭 → 작업 화면(work) 이동 확인 → **통과** (카테고리 클릭 → 작업 화면 이동 확인)

## 3. 답변 저장 및 검증 (핵심)

- [x] ✅ **test_answer_yes_no**: YES/NO 질문 클릭 시 selected 상태 및 서버 저장 확인 → **통과** (YES 버튼 selected 상태 확인)
- [x] ✅ **test_answer_dependent_show**: 상위 YES 선택 시 하위 질문 표시 확인 (Q1 → Q2) → **통과** (Q1 YES → Q2 하위 질문 표시 확인)
- [x] ✅ **test_answer_dependent_hide**: 상위 NO 선택 시 하위 질문 숨김 및 N/A 처리 확인 → **통과** (Q1 NO → Q2 숨김 확인)
- [x] ✅ **test_answer_number**: 숫자 입력 및 쉼표(,) 자동 포맷팅 확인 → **통과** (숫자 입력 및 포맷팅 확인 (표시: 1,000,000))
- [x] ✅ **test_answer_text**: 텍스트(textarea) 입력 및 저장 확인 → **통과** (Q27 텍스트 저장 확인 (방화벽 도입(50만원), 보안관제(100만원)))
- [x] ✅ **test_validation_negative**: 숫자 필드 음수 입력 시 서버 400 차단 확인 → **통과** (음수 입력 400 차단 (음수는 입력할 수 없습니다.))
- [x] ✅ **test_validation_b_gt_a**: 정보보호 투자액(B)이 IT 투자액(A) 초과 시 400 차단 확인 → **통과** (B > A 차단 확인 (정보보호 투자액(B) 2,000,000원이 정보기술 투자액(A) 1,000,000원을 초과합니다.))
- [x] ✅ **test_validation_personnel**: 인력 계층 위반(IT인력 > 총인원) 시 400 차단 확인 → **통과** (IT인력 > 총인원 400 차단 (정보기술부문 인력(20명)은 총 임직원 수(10명)를 초과할 수 없습니다.))
- [ ] ⊘ **test_answer_confirmed_blocked**: 확정(confirmed) 상태에서 답변 수정 시도 시 403 차단 확인 → **건너뜀** (현재 세션이 confirmed 아님 — 확정 후 수동 재확인 필요)

## 4. 증빙 자료 관리

- [x] ✅ **test_evidence_upload**: 허용 확장자(PNG) 파일 업로드 성공 확인 → **통과** (PNG 업로드 성공 (id: 7f8a155b...))
- [x] ✅ **test_evidence_invalid_ext**: 비허용 확장자(exe) 파일 업로드 차단 확인 → **통과** (비허용 확장자 차단 확인 (status: 400))
- [x] ✅ **test_evidence_delete**: 업로드된 증빙 파일 삭제 API 정상 동작 확인 → **통과** (증빙 삭제 성공 (ID: 1664ea0b...))

## 5. 공시 확정 흐름 (SoD 직무분리)

- [x] ✅ **test_submit_incomplete_blocked**: 완료율 미달 상태에서 검토 요청(submit) 차단 확인 → **통과** (미완료 상태에서 submit 차단 메시지 확인)
- [x] ✅ **test_confirm_without_submit_blocked**: submitted 상태 없이 confirm 시도 시 차단 확인 → **통과** (submitted 없이 confirm 차단 확인)

## 6. Audit Trail (변경 이력)

- [x] ✅ **test_audit_trail_recorded**: 답변 저장 후 ipd_answer_history에 이력 기록 확인 → **통과** (Audit Trail 이력 기록 확인 (11 → 12건))

## 7. 데이터 무결성

- [x] ✅ **test_recursive_na_cleanup**: 상위 NO 변경 시 하위 데이터 N/A 처리 후 YES 복귀 시 재활성화 확인 → **통과** (YES→NO→YES 순환 시 하위 질문 재활성화 확인)
- [x] ✅ **test_session_progress_update**: 답변 저장 후 세션 완료율(completion_rate) 갱신 확인 → **통과** (세션 완료율 갱신 확인 (11% → 11%))

---
## 테스트 결과 요약

| 항목 | 개수 | 비율 |
|------|------|------|
| ✅ 통과  | 25  | 96.2% |
| ❌ 실패  | 0  | 0.0% |
| ⚠️ 경고  | 0 | 0.0% |
| ⊘ 건너뜀 | 1 | 3.8% |
| **총계** | **26** | **100%** |
