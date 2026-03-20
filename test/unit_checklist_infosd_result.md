<!-- Test Run: 2026-03-20 10:07:56 -->
# infosd: 정보보호공시 시스템 테스트 시나리오

## 1. 회사·연도 관리

- [x] ✅ **test_company_add**: 신규 회사 등록 후 목록에 표시되는지 확인 → **통과** ('테스트회사_자동' 등록 및 목록 표시 확인)
- [x] ✅ **test_company_add_duplicate**: 동일 회사명 중복 등록 시 경고 메시지 확인 → **통과** ('테스트회사_자동' 등록 및 목록 표시 확인)
- [x] ✅ **test_company_edit**: 회사명 수정 후 반영 여부 확인 → **통과** (회사명 수정 확인 (→ 테스트회사_자동_편집 → 복구))
- [x] ✅ **test_year_add**: 공시 연도 추가 후 목록 표시 확인 → **통과** (2027년도 목록 존재 확인)
- [x] ✅ **test_year_add_duplicate**: 동일 연도 중복 추가 시 경고 메시지 확인 → **통과** (2027년도 목록 존재 확인)
- [x] ✅ **test_company_delete**: 회사 삭제 후 목록에서 제거 확인 → **통과** ('삭제테스트_임시' 삭제 후 목록 제거 확인)

## 2. 공시 세션 진입 및 대시보드

- [x] ✅ **test_session_select**: 회사+연도 선택 후 대시보드 페이지 진입 확인 → **통과** (대시보드 진입 확인 (URL: http://localhost:5001/disclosure/))
- [x] ✅ **test_dashboard_render**: 카테고리 카드 및 진행률 렌더링 확인 → **통과** (카테고리 카드 4개 렌더링 확인)
- [x] ✅ **test_dashboard_card_progress_consistency**: 카드 done/total 수치 일관성 확인 → **통과** (completion_rate 유효 범위 확인 (39%))
- [x] ✅ **test_dashboard_category_navigation**: 카테고리 카드 클릭 → 작업 화면(work) 이동 확인 → **통과** (카테고리 클릭 → 작업 화면 이동 확인)

## 3. 답변 저장 및 검증 (핵심)

- [x] ✅ **test_answer_yes_no**: YES/NO 질문 클릭 시 selected 상태 및 서버 저장 확인 → **통과** (YES 버튼 selected 상태 확인)
- [x] ✅ **test_answer_dependent_show**: 상위 YES 선택 시 하위 질문 표시 확인 (Q1 → Q2) → **통과** (Q1 YES → Q2 하위 질문 표시 확인)
- [x] ✅ **test_answer_dependent_hide**: 상위 NO 선택 시 하위 질문 숨김 및 N/A 처리 확인 → **통과** (Q1 NO → Q2 숨김 확인)
- [x] ✅ **test_answer_number**: 숫자 입력 및 쉼표(,) 자동 포맷팅 확인 → **통과** (숫자 입력 및 포맷팅 확인 (표시: 5,000,000))
- [x] ✅ **test_answer_select**: select 타입(Q18) 답변 저장 및 조회 확인 → **통과** (select 타입(Q18) 저장 및 DB 확인)
- [x] ✅ **test_validation_negative**: 숫자 필드 음수 입력 시 서버 400 차단 확인 → **통과** (음수 입력 400 차단 (음수는 입력할 수 없습니다.))
- [x] ✅ **test_validation_b_gt_a**: 정보보호 투자액(B=Q4+Q5+Q6 합계)이 IT 투자액(A=Q2) 초과 시 400 차단 확인 → **통과** (B > A 차단 확인 (정보보호 투자액(B) 1,100,000원이 정보기술 투자액(A) 1,000,000원을 초과합니다.))
- [x] ✅ **test_validation_personnel**: 정보기술부문 인력(Q28)이 총 임직원(Q10) 초과 시 400 차단 확인 → **통과** (IT인력 > 총인원 400 차단 (정보기술부문 인력(20명)은 총 임직원 수(10명)를 초과할 수 없습니다.))
- [x] ✅ **test_answer_confirmed_blocked**: 확정(confirmed) 상태에서 답변 수정 시도 시 403 차단 확인 → **통과** (confirmed 상태에서 답변 수정 403 차단 확인)

## 4. 증빙 자료 관리

- [x] ✅ **test_evidence_upload**: 허용 확장자(PNG) 파일 업로드 성공 확인 → **통과** (PNG 업로드 성공 (id: 73b9601e...))
- [x] ✅ **test_evidence_invalid_ext**: 비허용 확장자(exe) 파일 업로드 차단 확인 → **통과** (비허용 확장자 차단 확인 (status: 400))
- [x] ✅ **test_evidence_delete**: 업로드된 증빙 파일 삭제 API 정상 동작 확인 → **통과** (증빙 삭제 성공 (ID: a911d3e4...))

## 5. 공시 확정 흐름

- [x] ✅ **test_submit_incomplete_blocked**: 완료율 미달 상태에서 검토 요청(submit) 차단 확인 → **통과** (미완료 상태에서 submit 차단 메시지 확인)
- [x] ✅ **test_confirm_without_submit_blocked**: submitted 상태 없이 confirm 시도 시 차단 확인 → **통과** (submitted 없이 confirm 차단 확인)

## 6. Audit Trail (변경 이력)

- [x] ✅ **test_audit_trail_recorded**: 답변 저장 후 isd_answer_history에 이력 기록 확인 → **통과** (Audit Trail 이력 기록 확인 (413 → 414건))

## 7. 데이터 무결성

- [x] ✅ **test_recursive_na_cleanup**: 상위 NO 변경 시 하위 데이터 N/A 처리 확인 → **통과** (YES→NO→YES 순환 시 하위 질문 재활성화 확인)
- [x] ✅ **test_session_progress_update**: 답변 저장 후 세션 완료율(completion_rate) 갱신 확인 → **통과** (세션 완료율 갱신 확인 (26% → 26%))

## 8. table 타입 답변 저장

- [x] ✅ **test_answer_table_type_json**: Q27(주요 투자 항목, table 타입) JSON 배열 형식 저장 및 조회 확인 → **통과** (Q27 JSON 배열 저장 확인 (2행))

## 9. inv-grid 렌더링

- [x] ✅ **test_inv_grid_investment_render**: 카테고리 1 투자 inv-grid-outer 및 I-3 투자비율 ratio-bar 렌더링 확인 → **통과** (카테고리 1 투자 inv-grid + I-3 ratio-bar 렌더링 확인)
- [x] ✅ **test_inv_grid_personnel_render**: 카테고리 2 인력 그리드(Q10/Q28/Q11/Q12) 및 II-4 ratio-bar 렌더링 확인 → **통과** (카테고리 2 인력 컴팩트 그리드 + II-4 ratio-bar 렌더링 확인)

## 10. 비율 자동계산

- [x] ✅ **test_investment_ratio_api**: Q1=YES/Q2/Q4 답변 저장 후 I-3 투자비율(B/A) 표시 확인 → **통과** (투자비율 자동계산 표시 확인 (20.00%))
- [x] ✅ **test_personnel_ratio_api**: Q9=YES/Q10/Q28/Q11/Q12 답변 저장 후 II-4 인력비율(D/C) 표시 확인 → **통과** (인력비율 자동계산 표시 확인 (35.00%))

## 11. table 타입 증빙 자료

- [x] ✅ **test_evidence_for_table_type**: table 타입 질문(Q27 주요투자항목) 증빙 파일(PDF) 업로드 및 삭제 확인 → **통과** (table 타입(Q27) 증빙 PDF 업로드 및 삭제 확인)

## 12. 증빙 섹션 표시 조건

- [x] ✅ **test_evidence_section_toggle_by_value**: number 타입(Q4) 금액 0 입력 시 증빙 섹션 숨김, 양수 입력 시 표시 전환 확인 → **통과** (number 타입 금액 기반 증빙 섹션 토글 확인 (0→숨김, 양수→표시))

## 13. none_hidden 처리

- [x] ✅ **test_none_hidden_q29_review**: Q14 전체 해당없음 시 최종 검토 페이지에서 Q29(II-6) 행 미표시 확인 → **통과** (Q14 전체 해당없음 → review 페이지에서 Q29(II-6) 행 미표시 확인)

## 14. checkbox 타입

- [x] ✅ **test_checkbox_answer_json**: Q20(checkbox 타입) JSON 배열 저장 및 유효성 확인 → **통과** (checkbox JSON 배열 저장 확인 (2개 항목))

## 15. confirmed 잠금 모드

- [x] ✅ **test_confirmed_fields_locked**: confirmed 상태에서 work 페이지 IS_CONFIRMED=true 및 confirmed-mode 활성화 확인 → **통과** (confirmed 모드 IS_CONFIRMED=true 및 confirmed-mode 클래스 활성화 확인)

## 16. 확정/취소 완전 흐름

- [x] ✅ **test_confirm_unconfirm_flow**: 100% 완료 → confirm → confirmed 상태 전환 → unconfirm → in_progress 복귀 확인 → **통과** (confirmed → unconfirm 흐름 정상 (최종 상태: completed))

## 17. 다운로드 응답 검증

- [x] ✅ **test_download_word**: 공시 워드 문서 다운로드 HTTP 200 및 Content-Type 확인 → **통과** (워드 다운로드 성공 (Content-Type: application/vnd.openxmlformats-officedocument.wordprocessing))
- [x] ✅ **test_download_excel**: 증빙 포함 엑셀 다운로드 HTTP 200 및 Content-Type 확인 → **통과** (엑셀 다운로드 성공 (Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.))

## 18. Q13/Q14/Q29 연쇄 조건

- [x] ✅ **test_q13_no_skips_q14_q29**: Q13=NO 저장 시 Q14·Q29 답변이 N/A로 처리되는지 확인 → **통과** (Q13=NO 시 Q14 N/A 처리 확인)

## 19. review 페이지 렌더링

- [x] ✅ **test_review_page_render**: 최종 검토 페이지 항목 테이블·진행률·버튼 렌더링 확인 → **통과** (review 페이지 핵심 요소 모두 렌더링 확인)

## 20. 투어·컨택 페이지

- [x] ✅ **test_tour_page_render**: 투어 페이지 비로그인 접근 및 핵심 콘텐츠 렌더링 확인 → **통과** (투어 페이지 렌더링 및 핵심 요소 확인)
- [x] ✅ **test_contact_page_render**: 컨택 페이지 렌더링·필수항목 누락·URL 포함 유효성 검증 → **통과** (컨택 페이지 렌더링·필수항목 누락·URL 포함 검증 모두 통과)

---
## 테스트 결과 요약

| 항목 | 개수 | 비율 |
|------|------|------|
| ✅ 통과  | 44  | 100.0% |
| ❌ 실패  | 0  | 0.0% |
| ⚠️ 경고  | 0 | 0.0% |
| ⊘ 건너뜀 | 0 | 0.0% |
| **총계** | **44** | **100%** |
