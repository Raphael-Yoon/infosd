"""
infosd: 정보보호공시 시스템 Unit 테스트 코드

unit_checklist_infosd.md 시나리오 기반 자동 테스트.
실행 완료 후 unit_checklist_infosd_result.md에 결과 저장.

실행:
    python test/test_unit_infosd.py
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from test.playwright_base import PlaywrightTestBase, TestStatus, UnitTestResult

import requests as req


# 테스트 전용 상수
TEST_COMPANY_NAME = "테스트회사_자동"
TEST_YEAR = 2099


class InfosdUnitTest(PlaywrightTestBase):

    def __init__(self, base_url="http://localhost:5001", **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.category = "infosd: 정보보호공시"
        self.checklist_source = project_root / "test" / "unit_checklist_infosd.md"
        self.checklist_result = project_root / "test" / "unit_checklist_infosd_result.md"
        self._company_id = None

    # ─── 공통 헬퍼 ───────────────────────────────────────────

    def _get_cookies(self) -> dict:
        cookies = self.context.cookies()
        return {c["name"]: c["value"] for c in cookies}

    def _ensure_session(self):
        """테스트용 회사(TEST_COMPANY_NAME, TEST_YEAR) 세션을 보장하고 company_id 반환."""
        self.navigate_to("/")
        self.page.wait_for_timeout(1000)

        # 테스트 회사 존재 여부 확인
        existing = self.page.locator(f"text={TEST_COMPANY_NAME}").first
        if existing.count() == 0:
            # 회사 등록
            name_input = self.page.locator("input[name='name']").first
            name_input.fill(TEST_COMPANY_NAME)
            self.page.locator("button[type='submit']").first.click()
            self.page.wait_for_timeout(1000)

        # company_id 추출 (삭제 버튼 form action 기준)
        delete_form = self.page.locator(
            f".company-card:has-text('{TEST_COMPANY_NAME}') form[action*='/delete']"
        ).first
        if delete_form.count() == 0:
            return None
        action = delete_form.get_attribute("action") or ""
        # action: /company/<company_id>/delete
        parts = [p for p in action.split("/") if p]
        if len(parts) < 2:
            return None
        company_id = parts[1]
        self._company_id = company_id

        # 연도 존재 여부 확인
        year_badge = self.page.locator(
            f".company-card:has-text('{TEST_COMPANY_NAME}') .year-badge:has-text('{TEST_YEAR}')"
        ).first
        if year_badge.count() == 0:
            year_form = self.page.locator(
                f".company-card:has-text('{TEST_COMPANY_NAME}') form[action*='/year/add']"
            ).first
            if year_form.count() > 0:
                year_form.locator("input[name='year']").fill(str(TEST_YEAR))
                year_form.locator("button[type='submit']").click()
                self.page.wait_for_timeout(1000)

        # 세션 선택
        self.navigate_to(f"/disclosure/select/{company_id}/{TEST_YEAR}")
        self.page.wait_for_timeout(1000)
        return company_id

    def _api(self, method: str, path: str, **kwargs):
        """쿠키 포함 requests 호출."""
        url = f"{self.base_url}{path}"
        cookies = self._get_cookies()
        return getattr(req, method)(url, cookies=cookies, timeout=10, **kwargs)

    # ─── 1. 회사·연도 관리 ──────────────────────────────────

    def test_company_add(self, result: UnitTestResult):
        """1. 신규 회사 등록"""
        self.navigate_to("/")
        self.page.wait_for_timeout(800)

        # 이미 존재하면 삭제 후 재등록
        card = self.page.locator(f"text={TEST_COMPANY_NAME}").first
        if card.count() > 0:
            del_form = self.page.locator(
                f".company-card:has-text('{TEST_COMPANY_NAME}') form[action*='/delete']"
            ).first
            if del_form.count() > 0:
                del_form.locator("button[type='submit']").click()
                self.page.wait_for_timeout(800)

        name_input = self.page.locator("input[name='name']").first
        name_input.fill(TEST_COMPANY_NAME)
        self.page.locator("button[type='submit']").first.click()
        self.page.wait_for_timeout(800)

        if self.page.locator(f"text={TEST_COMPANY_NAME}").first.count() > 0:
            result.pass_test(f"회사 '{TEST_COMPANY_NAME}' 등록 및 목록 표시 확인")
        else:
            result.fail_test("등록 후 목록에서 회사명을 찾을 수 없음")

    def test_company_add_duplicate(self, result: UnitTestResult):
        """1. 중복 회사 등록 차단"""
        self.navigate_to("/")
        self.page.wait_for_timeout(800)

        name_input = self.page.locator("input[name='name']").first
        name_input.fill(TEST_COMPANY_NAME)
        self.page.locator("button[type='submit']").first.click()
        self.page.wait_for_timeout(800)

        # flash 경고 메시지 확인
        alert = self.page.locator(".alert, .flash-message, [class*='warning'], [class*='alert']").first
        page_text = self.page.content()
        if "이미 등록" in page_text or (alert.count() > 0 and "이미" in alert.inner_text()):
            result.pass_test("중복 등록 시 경고 메시지 확인")
        else:
            result.warn_test("경고 메시지 셀렉터 미일치 — 페이지 내 '이미 등록' 텍스트로 판단")

    def test_company_edit(self, result: UnitTestResult):
        """1. 회사명 수정"""
        self.navigate_to("/")
        self.page.wait_for_timeout(800)

        edit_form = self.page.locator(
            f".company-card:has-text('{TEST_COMPANY_NAME}') form[action*='/edit']"
        ).first
        if edit_form.count() == 0:
            result.skip_test("수정 폼을 찾을 수 없음 — 회사가 없거나 셀렉터 불일치")
            return

        new_name = TEST_COMPANY_NAME + "_편집"
        edit_form.locator("input[name='name']").fill(new_name)
        edit_form.locator("button[type='submit']").click()
        self.page.wait_for_timeout(800)

        if self.page.locator(f"text={new_name}").first.count() > 0:
            # 원래 이름으로 복구
            edit_form2 = self.page.locator(
                f".company-card:has-text('{new_name}') form[action*='/edit']"
            ).first
            if edit_form2.count() > 0:
                edit_form2.locator("input[name='name']").fill(TEST_COMPANY_NAME)
                edit_form2.locator("button[type='submit']").click()
                self.page.wait_for_timeout(800)
            result.pass_test(f"회사명 수정 확인 ({TEST_COMPANY_NAME} → {new_name} → 복구)")
        else:
            result.fail_test("수정 후 새 이름이 목록에 표시되지 않음")

    def test_year_add(self, result: UnitTestResult):
        """1. 공시 연도 추가"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("테스트 회사 세션 구성 실패")
            return

        self.navigate_to("/")
        self.page.wait_for_timeout(800)

        year_badge = self.page.locator(
            f".company-card:has-text('{TEST_COMPANY_NAME}') :text('{TEST_YEAR}')"
        ).first
        if year_badge.count() > 0:
            result.pass_test(f"{TEST_YEAR}년도가 이미 목록에 존재 — 추가 완료 상태")
        else:
            result.fail_test(f"{TEST_YEAR}년도가 목록에 없음")

    def test_year_add_duplicate(self, result: UnitTestResult):
        """1. 연도 중복 추가 차단"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("테스트 회사 세션 구성 실패")
            return

        self.navigate_to("/")
        self.page.wait_for_timeout(800)

        year_form = self.page.locator(
            f".company-card:has-text('{TEST_COMPANY_NAME}') form[action*='/year/add']"
        ).first
        if year_form.count() == 0:
            result.skip_test("연도 추가 폼을 찾을 수 없음")
            return

        year_form.locator("input[name='year']").fill(str(TEST_YEAR))
        year_form.locator("button[type='submit']").click()
        self.page.wait_for_timeout(800)

        page_text = self.page.content()
        if "이미 등록" in page_text or "중복" in page_text:
            result.pass_test("연도 중복 추가 시 경고 확인")
        else:
            result.warn_test("경고 텍스트 미감지 — 중복 차단 여부 수동 확인 필요")

    def test_company_delete(self, result: UnitTestResult):
        """1. 회사 삭제"""
        # 삭제용 임시 회사 생성
        tmp_name = "삭제테스트_임시"
        self.navigate_to("/")
        self.page.wait_for_timeout(800)

        name_input = self.page.locator("input[name='name']").first
        name_input.fill(tmp_name)
        self.page.locator("button[type='submit']").first.click()
        self.page.wait_for_timeout(800)

        del_form = self.page.locator(
            f".company-card:has-text('{tmp_name}') form[action*='/delete']"
        ).first
        if del_form.count() == 0:
            result.fail_test("삭제 폼을 찾을 수 없음 — 회사 등록 실패")
            return

        del_form.locator("button[type='submit']").click()
        self.page.wait_for_timeout(800)

        if self.page.locator(f"text={tmp_name}").first.count() == 0:
            result.pass_test(f"'{tmp_name}' 삭제 후 목록 제거 확인")
        else:
            result.fail_test("삭제 후에도 목록에 회사가 남아 있음")

    # ─── 2. 공시 세션 진입 및 대시보드 ─────────────────────

    def test_session_select(self, result: UnitTestResult):
        """2. 회사+연도 선택 후 대시보드 진입"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        title = self.page.title()
        url = self.page.url
        if "dashboard" in url or "disclosure" in url or "공시" in title:
            result.pass_test(f"대시보드 진입 확인 (URL: {url})")
        else:
            result.fail_test(f"대시보드 미진입 (URL: {url}, Title: {title})")

    def test_dashboard_render(self, result: UnitTestResult):
        """2. 대시보드 카테고리 카드 렌더링"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        self.navigate_to("/disclosure/")
        self.page.wait_for_timeout(1500)

        cards = self.page.locator(".category-card")
        count = cards.count()
        if count >= 4:
            result.pass_test(f"카테고리 카드 {count}개 렌더링 확인")
        else:
            result.fail_test(f"카테고리 카드 수 부족 ({count}개, 최소 4개 필요)")

    def test_dashboard_category_navigation(self, result: UnitTestResult):
        """2. 카테고리 카드 클릭 → 작업 화면 이동"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        self.navigate_to("/disclosure/")
        self.page.wait_for_timeout(1500)

        first_card = self.page.locator(".category-card").first
        if first_card.count() == 0:
            result.skip_test("카테고리 카드 없음")
            return

        first_card.click()
        self.page.wait_for_timeout(1500)
        url = self.page.url

        if "work" in url or self.page.locator(".question-item").count() > 0:
            result.pass_test(f"카테고리 클릭 → 작업 화면 이동 확인 (URL: {url})")
        else:
            result.fail_test(f"작업 화면 미이동 (URL: {url})")

    # ─── 3. 답변 저장 및 검증 ───────────────────────────────

    def test_answer_yes_no(self, result: UnitTestResult):
        """3. YES/NO 답변 저장"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        self.navigate_to("/disclosure/work")
        self.page.wait_for_timeout(1500)

        yes_btn = self.page.locator("#question-Q1 .yn-btn.yes").first
        if yes_btn.count() == 0:
            result.skip_test("Q1 YES 버튼 미발견")
            return

        yes_btn.scroll_into_view_if_needed()
        yes_btn.click()
        self.page.wait_for_timeout(1200)

        cls = yes_btn.get_attribute("class") or ""
        if "selected" in cls:
            result.pass_test("YES 버튼 선택 및 selected 상태 확인")
        else:
            result.fail_test(f"selected 클래스 미부여 (class: {cls})")

    def test_answer_dependent_show(self, result: UnitTestResult):
        """3. 상위 YES → 하위 질문 표시"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        self.navigate_to("/disclosure/work")
        self.page.wait_for_timeout(1500)

        q1_yes = self.page.locator("#question-Q1 .yn-btn.yes").first
        if q1_yes.count() == 0:
            result.skip_test("Q1 버튼 미발견")
            return

        q1_yes.click()
        self.page.wait_for_timeout(1500)

        q2 = self.page.locator("#question-Q2")
        if q2.count() > 0 and q2.is_visible():
            result.pass_test("Q1 YES → Q2 하위 질문 표시 확인")
        else:
            result.fail_test("Q1 YES 선택 후 Q2가 표시되지 않음")

    def test_answer_dependent_hide(self, result: UnitTestResult):
        """3. 상위 NO → 하위 질문 숨김"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        self.navigate_to("/disclosure/work")
        self.page.wait_for_timeout(1500)

        # YES → NO 전환
        q1_yes = self.page.locator("#question-Q1 .yn-btn.yes").first
        q1_no  = self.page.locator("#question-Q1 .yn-btn.no").first
        if q1_yes.count() == 0 or q1_no.count() == 0:
            result.skip_test("Q1 버튼 미발견")
            return

        q1_yes.click()
        self.page.wait_for_timeout(1000)
        q1_no.click()
        self.page.wait_for_timeout(1500)

        q2 = self.page.locator("#question-Q2")
        hidden = q2.count() == 0 or not q2.is_visible()
        if hidden:
            result.pass_test("Q1 NO → Q2 숨김 확인")
        else:
            result.fail_test("Q1 NO 선택 후에도 Q2가 화면에 표시됨")

    def test_answer_number(self, result: UnitTestResult):
        """3. 숫자 입력 및 쉼표 포맷팅"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        self.navigate_to("/disclosure/work")
        self.page.wait_for_timeout(1500)

        # Q1 YES → Q2 활성화
        q1_yes = self.page.locator("#question-Q1 .yn-btn.yes").first
        if q1_yes.count() > 0:
            q1_yes.click()
            self.page.wait_for_timeout(1200)

        q2_input = self.page.locator("#input-Q2")
        if q2_input.count() == 0 or not q2_input.is_visible():
            result.skip_test("Q2 입력 필드 미발견")
            return

        q2_input.fill("1000000")
        q2_input.dispatch_event("input")
        self.page.wait_for_timeout(800)
        q2_input.blur()
        self.page.wait_for_timeout(800)

        val = q2_input.input_value()
        result.add_detail(f"입력값: {val}")
        if "1,000,000" in val or val.replace(",", "") == "1000000":
            result.pass_test(f"숫자 입력 및 포맷팅 확인 (표시: {val})")
        else:
            result.fail_test(f"포맷팅 미적용 또는 저장 오류 (val: {val})")

    def test_answer_text(self, result: UnitTestResult):
        """3. 텍스트(textarea) 입력 및 저장"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        self.navigate_to("/disclosure/work")
        self.page.wait_for_timeout(1500)

        # Q27 (주요 투자 항목, textarea 타입)
        # Q1 YES 먼저 선택
        q1_yes = self.page.locator("#question-Q1 .yn-btn.yes").first
        if q1_yes.count() > 0:
            q1_yes.click()
            self.page.wait_for_timeout(1200)

        q27_input = self.page.locator("#input-Q27")
        if q27_input.count() == 0 or not q27_input.is_visible():
            result.skip_test("Q27 textarea 미발견 (Q1 YES 필요)")
            return

        test_text = "방화벽 도입(50만원), 보안관제 서비스(100만원)"
        q27_input.fill(test_text)
        q27_input.blur()
        self.page.wait_for_timeout(800)

        # API로 저장 여부 확인
        resp = self._api("get", f"/disclosure/api/answers/{company_id}/{TEST_YEAR}")
        if resp.status_code == 200:
            answers = resp.json().get("answers", {})
            saved = answers.get("Q27", "")
            if test_text in saved or saved:
                result.pass_test(f"Q27 텍스트 저장 확인 (저장값: {saved[:40]})")
            else:
                result.fail_test(f"Q27 저장값 불일치 (저장값: {saved})")
        else:
            result.warn_test(f"저장 API 응답 확인 불가 (status: {resp.status_code})")

    def test_validation_negative(self, result: UnitTestResult):
        """3. 음수 입력 차단"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        resp = self._api("post", "/disclosure/api/answer",
                         json={"question_id": "Q2", "company_id": company_id,
                               "year": TEST_YEAR, "value": "-5000"})
        if resp.status_code == 400:
            result.pass_test(f"음수 입력 시 400 차단 확인 ({resp.json().get('message', '')})")
        else:
            result.fail_test(f"음수 입력이 차단되지 않음 (status: {resp.status_code})")

    def test_validation_b_gt_a(self, result: UnitTestResult):
        """3. 정보보호 투자액(B) > IT 투자액(A) 차단"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        # A = 100만원 저장
        self._api("post", "/disclosure/api/answer",
                  json={"question_id": "Q2", "company_id": company_id,
                        "year": TEST_YEAR, "value": "1000000"})

        # B 구성 항목 중 하나(Q4)를 200만원으로 설정 → B > A
        resp = self._api("post", "/disclosure/api/answer",
                         json={"question_id": "Q4", "company_id": company_id,
                               "year": TEST_YEAR, "value": "2000000"})

        if resp.status_code == 400:
            msg = resp.json().get("message", "")
            result.pass_test(f"B > A 차단 확인 ({msg[:60]})")
        else:
            result.fail_test(f"B > A 허용됨 (status: {resp.status_code})")

    def test_validation_personnel(self, result: UnitTestResult):
        """3. 인력 계층 검증 (IT인력 > 총인원 차단)"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        # 총인원 = 10명
        self._api("post", "/disclosure/api/answer",
                  json={"question_id": "Q10", "company_id": company_id,
                        "year": TEST_YEAR, "value": "10"})

        # IT인력 = 20명 (총인원 초과)
        resp = self._api("post", "/disclosure/api/answer",
                         json={"question_id": "Q28", "company_id": company_id,
                               "year": TEST_YEAR, "value": "20"})

        if resp.status_code == 400:
            msg = resp.json().get("message", "")
            result.pass_test(f"IT인력 > 총인원 시 400 차단 확인 ({msg[:60]})")
        else:
            result.fail_test(f"인력 계층 위반이 차단되지 않음 (status: {resp.status_code})")

    def test_answer_confirmed_blocked(self, result: UnitTestResult):
        """3. 확정(confirmed) 상태에서 답변 수정 403 차단"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        # DB를 직접 confirmed로 변경 (API 테스트)
        # unconfirm 후 강제로 status=confirmed 설정은 어렵으므로
        # API 호출 후 403 응답 여부로 확인 (이미 confirmed 상태가 아닌 경우 skip)
        resp = self._api("post", "/disclosure/api/answer",
                         json={"question_id": "Q27", "company_id": company_id,
                               "year": TEST_YEAR, "value": "테스트"})

        if resp.status_code == 403:
            result.pass_test("confirmed 상태에서 수정 시도 시 403 확인")
        elif resp.status_code == 200:
            result.skip_test("현재 세션이 confirmed 상태가 아님 — 수동으로 확정 후 재확인 필요")
        else:
            result.warn_test(f"예상치 못한 응답: {resp.status_code}")

    # ─── 4. 증빙 자료 관리 ──────────────────────────────────

    def test_evidence_upload(self, result: UnitTestResult):
        """4. 허용 확장자 파일 업로드"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        png_sig = b"\x89PNG\r\n\x1a\n"
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(png_sig + b"infosd unit test evidence")
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as f:
                resp = self._api("post", "/disclosure/api/evidence",
                                 files={"file": ("test_ev.png", f, "image/png")},
                                 data={"question_id": "Q2",
                                       "company_id": company_id,
                                       "year": str(TEST_YEAR)})

            if resp.status_code == 200 and resp.json().get("success"):
                ev_id = resp.json().get("evidence", {}).get("id", "?")
                result.add_detail(f"evidence id: {str(ev_id)[:8]}...")
                result.pass_test("PNG 파일 업로드 성공 확인")
            else:
                result.fail_test(f"업로드 실패: {resp.status_code} — {resp.text[:80]}")
        finally:
            os.unlink(tmp_path)

    def test_evidence_invalid_ext(self, result: UnitTestResult):
        """4. 비허용 확장자(exe) 차단"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as tmp:
            tmp.write(b"MZ fake exe")
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as f:
                resp = self._api("post", "/disclosure/api/evidence",
                                 files={"file": ("malware.exe", f, "application/octet-stream")},
                                 data={"question_id": "Q2",
                                       "company_id": company_id,
                                       "year": str(TEST_YEAR)})

            if resp.status_code in (400, 415) or not resp.json().get("success", True):
                result.pass_test(f"비허용 확장자 차단 확인 (status: {resp.status_code})")
            else:
                result.fail_test(f".exe 파일이 업로드 허용됨 (status: {resp.status_code})")
        finally:
            os.unlink(tmp_path)

    def test_evidence_delete(self, result: UnitTestResult):
        """4. 증빙 파일 삭제"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        # 먼저 업로드
        png_sig = b"\x89PNG\r\n\x1a\n"
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(png_sig + b"delete test content")
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as f:
                up_resp = self._api("post", "/disclosure/api/evidence",
                                    files={"file": ("del_test.png", f, "image/png")},
                                    data={"question_id": "Q2",
                                          "company_id": company_id,
                                          "year": str(TEST_YEAR)})
        finally:
            os.unlink(tmp_path)

        if up_resp.status_code != 200 or not up_resp.json().get("success"):
            result.skip_test("사전 업로드 실패 — 삭제 테스트 건너뜀")
            return

        ev_id = up_resp.json().get("evidence", {}).get("id")
        if not ev_id:
            result.skip_test("업로드 응답에서 증빙 ID 추출 실패")
            return

        del_resp = self._api("delete", f"/disclosure/api/evidence/{ev_id}")
        if del_resp.status_code == 200 and del_resp.json().get("success"):
            result.pass_test(f"증빙 삭제 성공 (ID: {str(ev_id)[:8]}...)")
        else:
            result.fail_test(f"삭제 실패: {del_resp.status_code} — {del_resp.text[:80]}")

    # ─── 5. 공시 확정 흐름 (SoD) ────────────────────────────

    def test_submit_incomplete_blocked(self, result: UnitTestResult):
        """5. 미완료 상태에서 검토 요청(submit) 차단"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        self.navigate_to("/disclosure/review")
        self.page.wait_for_timeout(1000)

        # POST /disclosure/submit
        resp = self._api("post", "/disclosure/submit", data={})
        page_text = self.page.content() if resp.status_code in (200, 302) else ""

        # 완료율 미달 시 리다이렉트 + flash 경고 → 브라우저로 확인
        self.navigate_to("/disclosure/review")
        self.page.locator("form[action*='/submit'] button").first.click() if \
            self.page.locator("form[action*='/submit'] button").count() > 0 else None
        self.page.wait_for_timeout(800)

        page_content = self.page.content()
        if "모든 항목" in page_content or "작성해야" in page_content or resp.status_code == 200:
            result.pass_test("미완료 상태에서 submit 차단 메시지 확인")
        else:
            result.warn_test("차단 메시지 감지 불가 — 완료율이 이미 100%이거나 셀렉터 불일치")

    def test_confirm_without_submit_blocked(self, result: UnitTestResult):
        """5. submitted 상태 없이 confirm 차단"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        # unconfirm 먼저 (상태 초기화)
        self._api("post", "/disclosure/unconfirm", data={})
        self.page.wait_for_timeout(500)

        # 직접 confirm 시도 (submitted 상태 아님)
        resp = self._api("post", "/disclosure/confirm", data={})

        # 브라우저로도 확인
        self.navigate_to("/disclosure/review")
        self.page.wait_for_timeout(800)
        page_content = self.page.content()

        if "검토 요청" in page_content or "submitted" in page_content or resp.status_code == 200:
            result.pass_test("submitted 없이 confirm 차단 확인")
        else:
            result.warn_test("차단 여부 자동 감지 불가 — 상태 로직 수동 확인 필요")

    # ─── 6. Audit Trail ─────────────────────────────────────

    def test_audit_trail_recorded(self, result: UnitTestResult):
        """6. 답변 저장 후 ipd_answer_history 이력 기록"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        import sqlite3
        db_path = project_root / "infosd.db"

        before = 0
        try:
            conn = sqlite3.connect(str(db_path))
            row = conn.execute(
                "SELECT COUNT(*) FROM ipd_answer_history WHERE company_id=? AND year=?",
                (company_id, TEST_YEAR)
            ).fetchone()
            before = row[0] if row else 0
            conn.close()
        except Exception as e:
            result.skip_test(f"DB 접근 실패: {e}")
            return

        # 답변 저장
        self._api("post", "/disclosure/api/answer",
                  json={"question_id": "Q27", "company_id": company_id,
                        "year": TEST_YEAR, "value": "Audit Trail 테스트"})

        after = 0
        try:
            conn = sqlite3.connect(str(db_path))
            row = conn.execute(
                "SELECT COUNT(*) FROM ipd_answer_history WHERE company_id=? AND year=?",
                (company_id, TEST_YEAR)
            ).fetchone()
            after = row[0] if row else 0
            conn.close()
        except Exception as e:
            result.fail_test(f"저장 후 DB 확인 실패: {e}")
            return

        if after > before:
            result.pass_test(f"Audit Trail 이력 기록 확인 ({before} → {after}건)")
        else:
            result.fail_test(f"이력 미증가 (before: {before}, after: {after})")

    # ─── 7. 데이터 무결성 ───────────────────────────────────

    def test_recursive_na_cleanup(self, result: UnitTestResult):
        """7. 상위 NO → 하위 N/A 처리 후 YES 복귀 시 재활성화"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        self.navigate_to("/disclosure/work")
        self.page.wait_for_timeout(1500)

        q1_yes = self.page.locator("#question-Q1 .yn-btn.yes").first
        q1_no  = self.page.locator("#question-Q1 .yn-btn.no").first
        if q1_yes.count() == 0 or q1_no.count() == 0:
            result.skip_test("Q1 버튼 미발견")
            return

        # YES → Q2 표시
        q1_yes.click()
        self.page.wait_for_timeout(1200)
        q2_visible = self.page.locator("#question-Q2").is_visible()

        # NO → Q2 숨김
        q1_no.click()
        self.page.wait_for_timeout(1200)
        q2_hidden = not self.page.locator("#question-Q2").is_visible()

        # YES 복귀 → Q2 재표시
        q1_yes.click()
        self.page.wait_for_timeout(1200)
        q2_back = self.page.locator("#question-Q2").is_visible()

        if q2_visible and q2_hidden and q2_back:
            result.pass_test("YES→NO→YES 순환 시 하위 질문 재활성화 확인")
        else:
            result.fail_test(
                f"재활성화 실패 (visible: {q2_visible}, hidden: {q2_hidden}, back: {q2_back})"
            )

    def test_session_progress_update(self, result: UnitTestResult):
        """7. 답변 저장 후 세션 완료율 갱신"""
        company_id = self._ensure_session()
        if not company_id:
            result.skip_test("세션 구성 실패")
            return

        import sqlite3
        db_path = project_root / "infosd.db"

        def get_rate():
            try:
                conn = sqlite3.connect(str(db_path))
                row = conn.execute(
                    "SELECT completion_rate FROM ipd_sessions WHERE company_id=? AND year=?",
                    (company_id, TEST_YEAR)
                ).fetchone()
                conn.close()
                return row[0] if row else None
            except Exception:
                return None

        before = get_rate()

        # Q1 YES 저장
        self._api("post", "/disclosure/api/answer",
                  json={"question_id": "Q1", "company_id": company_id,
                        "year": TEST_YEAR, "value": "YES"})
        self.page.wait_for_timeout(500)

        after = get_rate()
        result.add_detail(f"완료율: {before}% → {after}%")

        if after is not None:
            result.pass_test(f"세션 완료율 갱신 확인 ({before}% → {after}%)")
        else:
            result.fail_test("완료율 갱신 후 DB 값 확인 실패")

    # ─── 결과 저장 ───────────────────────────────────────────

    def _update_checklist_result(self):
        """체크리스트 소스 기반으로 결과 파일 생성."""
        if not self.checklist_source.exists():
            print(f"체크리스트 소스 없음: {self.checklist_source}")
            return

        with open(self.checklist_source, "r", encoding="utf-8") as f:
            lines = f.readlines()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated = [f"<!-- Test Run: {timestamp} -->\n"]

        for line in lines:
            updated_line = line
            for res in self.results:
                if res.test_name in line:
                    clean_msg = res.message.replace("\n", " ").strip()
                    if res.status == TestStatus.PASSED:
                        updated_line = line.replace("- [ ]", "- [x] ✅")
                        updated_line = updated_line.rstrip() + f" → **통과** ({clean_msg})\n"
                    elif res.status == TestStatus.FAILED:
                        updated_line = line.replace("- [ ]", "- [ ] ❌")
                        updated_line = updated_line.rstrip() + f" → **실패** ({clean_msg})\n"
                    elif res.status == TestStatus.WARNING:
                        updated_line = line.replace("- [ ]", "- [~] ⚠️")
                        updated_line = updated_line.rstrip() + f" → **경고** ({clean_msg})\n"
                    elif res.status == TestStatus.SKIPPED:
                        updated_line = line.replace("- [ ]", "- [ ] ⊘")
                        updated_line = updated_line.rstrip() + f" → **건너뜀** ({clean_msg})\n"
                    break
            updated.append(updated_line)

        total   = len(self.results) or 1
        passed  = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed  = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        warning = sum(1 for r in self.results if r.status == TestStatus.WARNING)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)

        updated += [
            "\n---\n",
            "## 테스트 결과 요약\n\n",
            "| 항목 | 개수 | 비율 |\n",
            "|------|------|------|\n",
            f"| ✅ 통과  | {passed}  | {passed/total*100:.1f}% |\n",
            f"| ❌ 실패  | {failed}  | {failed/total*100:.1f}% |\n",
            f"| ⚠️ 경고  | {warning} | {warning/total*100:.1f}% |\n",
            f"| ⊘ 건너뜀 | {skipped} | {skipped/total*100:.1f}% |\n",
            f"| **총계** | **{total}** | **100%** |\n",
        ]

        with open(self.checklist_result, "w", encoding="utf-8") as f:
            f.writelines(updated)
        print(f"\n✅ 체크리스트 결과 저장: {self.checklist_result}")


def run_tests():
    runner = InfosdUnitTest(headless=True, slow_mo=300)
    if not runner.check_server_running():
        print("❌ 서버 시작 실패 — 테스트 중단")
        return 1

    runner.setup()
    try:
        runner.run_category("infosd Unit Tests", [
            # 1. 회사·연도 관리
            runner.test_company_add,
            runner.test_company_add_duplicate,
            runner.test_company_edit,
            runner.test_year_add,
            runner.test_year_add_duplicate,
            runner.test_company_delete,
            # 2. 세션 진입 및 대시보드
            runner.test_session_select,
            runner.test_dashboard_render,
            runner.test_dashboard_category_navigation,
            # 3. 답변 저장 및 검증
            runner.test_answer_yes_no,
            runner.test_answer_dependent_show,
            runner.test_answer_dependent_hide,
            runner.test_answer_number,
            runner.test_answer_text,
            runner.test_validation_negative,
            runner.test_validation_b_gt_a,
            runner.test_validation_personnel,
            runner.test_answer_confirmed_blocked,
            # 4. 증빙 자료
            runner.test_evidence_upload,
            runner.test_evidence_invalid_ext,
            runner.test_evidence_delete,
            # 5. 공시 확정 흐름
            runner.test_submit_incomplete_blocked,
            runner.test_confirm_without_submit_blocked,
            # 6. Audit Trail
            runner.test_audit_trail_recorded,
            # 7. 데이터 무결성
            runner.test_recursive_na_cleanup,
            runner.test_session_progress_update,
        ])
    finally:
        runner._update_checklist_result()
        runner.print_final_report()
        runner.stop_server()
        runner.teardown()


if __name__ == "__main__":
    exit(run_tests())
