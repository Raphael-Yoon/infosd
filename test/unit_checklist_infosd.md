# infosd: 정보보호공시 시스템 테스트 시나리오

## 1. 회사·연도 관리

- [ ] **test_company_add**: 신규 회사 등록 후 목록에 표시되는지 확인
- [ ] **test_company_add_duplicate**: 동일 회사명 중복 등록 시 경고 메시지 확인
- [ ] **test_company_edit**: 회사명 수정 후 반영 여부 확인
- [ ] **test_year_add**: 공시 연도(2099) 추가 후 목록 표시 확인
- [ ] **test_year_add_duplicate**: 동일 연도 중복 추가 시 경고 메시지 확인
- [ ] **test_company_delete**: 회사 삭제 후 목록에서 제거 확인

## 2. 공시 세션 진입 및 대시보드

- [ ] **test_session_select**: 회사+연도 선택 후 대시보드 페이지 진입 확인
- [ ] **test_dashboard_render**: 4개 카테고리 카드 및 진행률 렌더링 확인
- [ ] **test_dashboard_category_navigation**: 카테고리 카드 클릭 → 작업 화면(work) 이동 확인

## 3. 답변 저장 및 검증 (핵심)

- [ ] **test_answer_yes_no**: YES/NO 질문 클릭 시 selected 상태 및 서버 저장 확인
- [ ] **test_answer_dependent_show**: 상위 YES 선택 시 하위 질문 표시 확인 (Q1 → Q2)
- [ ] **test_answer_dependent_hide**: 상위 NO 선택 시 하위 질문 숨김 및 N/A 처리 확인
- [ ] **test_answer_number**: 숫자 입력 및 쉼표(,) 자동 포맷팅 확인
- [ ] **test_answer_text**: 텍스트(textarea) 입력 및 저장 확인
- [ ] **test_validation_negative**: 숫자 필드 음수 입력 시 서버 400 차단 확인
- [ ] **test_validation_b_gt_a**: 정보보호 투자액(B)이 IT 투자액(A) 초과 시 400 차단 확인
- [ ] **test_validation_personnel**: 인력 계층 위반(IT인력 > 총인원) 시 400 차단 확인
- [ ] **test_answer_confirmed_blocked**: 확정(confirmed) 상태에서 답변 수정 시도 시 403 차단 확인

## 4. 증빙 자료 관리

- [ ] **test_evidence_upload**: 허용 확장자(PNG) 파일 업로드 성공 확인
- [ ] **test_evidence_invalid_ext**: 비허용 확장자(exe) 파일 업로드 차단 확인
- [ ] **test_evidence_delete**: 업로드된 증빙 파일 삭제 API 정상 동작 확인

## 5. 공시 확정 흐름 (SoD 직무분리)

- [ ] **test_submit_incomplete_blocked**: 완료율 미달 상태에서 검토 요청(submit) 차단 확인
- [ ] **test_confirm_without_submit_blocked**: submitted 상태 없이 confirm 시도 시 차단 확인

## 6. Audit Trail (변경 이력)

- [ ] **test_audit_trail_recorded**: 답변 저장 후 ipd_answer_history에 이력 기록 확인

## 7. 데이터 무결성

- [ ] **test_recursive_na_cleanup**: 상위 NO 변경 시 하위 데이터 N/A 처리 후 YES 복귀 시 재활성화 확인
- [ ] **test_session_progress_update**: 답변 저장 후 세션 완료율(completion_rate) 갱신 확인

## 8. table 타입 답변 저장

- [ ] **test_answer_table_type_json**: Q27(주요 투자 항목, table 타입) JSON 배열 형식 저장 및 조회 확인

## 9. inv-grid 렌더링

- [ ] **test_inv_grid_investment_render**: 카테고리 1 투자 inv-grid 및 I-3 투자비율 ratio-bar 렌더링 확인
- [ ] **test_inv_grid_personnel_render**: 카테고리 2 인력 컴팩트 그리드(Q10/Q28/Q11/Q12) 및 II-4 ratio-bar 렌더링 확인

## 10. 비율 자동계산

- [ ] **test_investment_ratio_api**: Q2/Q4 답변 저장 후 I-3 투자비율(B/A) 자동계산 표시 확인
- [ ] **test_personnel_ratio_api**: Q10/Q28/Q11/Q12 답변 저장 후 II-4 인력비율(D/C) 자동계산 표시 확인

## 11. table 타입 증빙 자료

- [ ] **test_evidence_for_table_type**: table 타입 질문(Q29 CISO 활동내역) 증빙 파일(PDF) 업로드 및 삭제 확인

## 12. 증빙 섹션 표시 조건

- [ ] **test_evidence_section_toggle_by_value**: number 타입 금액 0 입력 시 증빙 섹션 숨김, 양수 입력 시 표시 전환 확인
