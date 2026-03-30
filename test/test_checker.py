"""
infosd: 정보보호공시 대상 판별 체커 테스트

판별 로직(_decide_next) 단위 테스트 + HTTP 통합 테스트.

실행:
    python test/test_checker.py
"""

import sys
import requests
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from checker_routes import _decide_next, STEPS, RESULTS
from test.playwright_base import TestStatus, UnitTestResult

BASE_URL = "http://127.0.0.1:5001"
W = 60


# ============================================================
# 헬퍼
# ============================================================

def h(step_id, answer):
    """이력 항목 생성 헬퍼"""
    return {'step': step_id, 'answer': answer, 'question': '', 'answer_label': answer}


def build_history(*pairs):
    """(step_id, answer) 쌍으로 이력 생성"""
    return [h(sid, ans) for sid, ans in pairs]


# ============================================================
# 단위 테스트: _decide_next 판별 로직
# ============================================================

class CheckerUnitTests:
    def __init__(self):
        self.results: list[UnitTestResult] = []

    def _run(self, name, func):
        r = UnitTestResult(name)
        r.start()
        try:
            func()
            r.finish(TestStatus.PASSED)
        except AssertionError as e:
            r.finish(TestStatus.FAILED, str(e))
        except Exception as e:
            r.finish(TestStatus.FAILED, f"예외: {e}")
        self.results.append(r)

    # ── 경로 1: 상장 YES → MANDATORY_2027 즉시 ──────────────────
    def test_listed_yes(self):
        def fn():
            kind, key, _ = _decide_next('step1', 'YES', [])
            assert kind == 'result', "result 여야 함"
            assert key == 'MANDATORY_2027', f"MANDATORY_2027 여야 하는데 {key}"
        self._run("step1 상장=YES → MANDATORY_2027 즉시 확정", fn)

    # ── 경로 2: 상장 NO → ISMS YES → MANDATORY_2027 즉시 ────────
    def test_isms_yes(self):
        def fn():
            hist = build_history(('step1', 'NO'))
            kind, key, _ = _decide_next('step2', 'YES', hist)
            assert kind == 'result'
            assert key == 'MANDATORY_2027', f"{key}"
        self._run("step2 ISMS=YES → MANDATORY_2027 즉시 확정", fn)

    # ── 경로 3: step3(정보통신서비스)=NO → VOLUNTARY 즉시 ────────
    def test_not_icsp(self):
        def fn():
            hist = build_history(('step1', 'NO'), ('step2', 'NO'))
            kind, key, _ = _decide_next('step3', 'NO', hist)
            assert kind == 'result'
            assert key == 'VOLUNTARY', f"{key}"
        self._run("step3 정보통신서비스=NO → VOLUNTARY 즉시 종료", fn)

    # ── 경로 4: ICSP YES → 매출액 YES → MANDATORY ────────────────
    def test_revenue_yes(self):
        def fn():
            hist = build_history(('step1','NO'),('step2','NO'),('step3','YES'),('step4','YES'))
            # step4에서 YES
            kind, key, _ = _decide_next('step4', 'YES', hist)
            assert kind == 'result'
            assert key == 'MANDATORY', f"{key}"
        self._run("step4 매출액=YES → MANDATORY 즉시 확정", fn)

    # ── 경로 5: 매출액 NO → 이용자 YES → MANDATORY ───────────────
    def test_users_yes(self):
        def fn():
            hist = build_history(('step1','NO'),('step2','NO'),('step3','YES'),('step4','NO'))
            kind, key, _ = _decide_next('step5', 'YES', hist)
            assert kind == 'result'
            assert key == 'MANDATORY', f"{key}"
        self._run("step5 이용자수=YES → MANDATORY 즉시 확정", fn)

    # ── 경로 6: 매출액 NO, 이용자 NO, 특수업종 YES → SPECIAL_INDUSTRY
    def test_special_industry(self):
        def fn():
            hist = build_history(
                ('step1','NO'),('step2','NO'),('step3','YES'),
                ('step4','NO'),('step5','NO')
            )
            kind, key, _ = _decide_next('step6', 'YES', hist)
            assert kind == 'result'
            assert key == 'SPECIAL_INDUSTRY', f"{key}"
        self._run("step6 특수업종=YES → SPECIAL_INDUSTRY (매출·이용자 모두 NO 후)", fn)

    # ── 경로 7: 전 기준 미달 → VOLUNTARY ─────────────────────────
    def test_all_no(self):
        def fn():
            hist = build_history(
                ('step1','NO'),('step2','NO'),('step3','YES'),
                ('step4','NO'),('step5','NO')
            )
            kind, key, _ = _decide_next('step6', 'NO', hist)
            assert kind == 'result'
            assert key == 'VOLUNTARY', f"{key}"
        self._run("step6 특수업종=NO → VOLUNTARY (전 기준 미달)", fn)

    # ── 분기 확인: step3=YES → step4로 이동 ──────────────────────
    def test_icsp_yes_goto_step4(self):
        def fn():
            hist = build_history(('step1','NO'),('step2','NO'))
            kind, nxt = _decide_next('step3', 'YES', hist)[:2]
            assert kind == 'step'
            assert nxt == 'step4', f"step4 여야 하는데 {nxt}"
        self._run("step3 정보통신서비스=YES → step4로 진행", fn)

    # ── 분기 확인: step4=NO → step5로 이동 ───────────────────────
    def test_revenue_no_goto_step5(self):
        def fn():
            hist = build_history(('step1','NO'),('step2','NO'),('step3','YES'))
            kind, nxt = _decide_next('step4', 'NO', hist)[:2]
            assert kind == 'step'
            assert nxt == 'step5', f"step5 여야 하는데 {nxt}"
        self._run("step4 매출액=NO → step5로 진행", fn)

    # ── 분기 확인: step5=NO → step6으로 이동 ─────────────────────
    def test_users_no_goto_step6(self):
        def fn():
            hist = build_history(('step1','NO'),('step2','NO'),('step3','YES'),('step4','NO'))
            kind, nxt = _decide_next('step5', 'NO', hist)[:2]
            assert kind == 'step'
            assert nxt == 'step6', f"step6 여야 하는데 {nxt}"
        self._run("step5 이용자수=NO → step6(특수업종)으로 진행", fn)

    # ── 특수업종 질문은 매출액·이용자 모두 NO일 때만 도달 확인 ───
    def test_special_industry_not_reached_if_mandatory(self):
        def fn():
            # 매출액 YES면 MANDATORY로 즉시 종료 → step6 미도달
            hist = build_history(('step1','NO'),('step2','NO'),('step3','YES'))
            kind, key, _ = _decide_next('step4', 'YES', hist)
            assert kind == 'result'
            assert key == 'MANDATORY'
            # 결과가 MANDATORY이므로 step6(특수업종)은 호출되지 않음
        self._run("매출액 YES 시 특수업종 질문 미도달 확인", fn)

    # ── STEPS 정의 무결성: 모든 step에 필수 키 존재 ──────────────
    def test_steps_schema(self):
        def fn():
            required = {'id', 'title', 'question', 'hint', 'choices', 'progress_max'}
            for sid, step in STEPS.items():
                missing = required - set(step.keys())
                assert not missing, f"{sid} 에 누락된 키: {missing}"
                assert len(step['choices']) >= 2, f"{sid} choices 2개 이상이어야 함"
                assert step['progress_max'] == 6, f"{sid} progress_max=6 이어야 함"
        self._run("STEPS 딕셔너리 스키마 무결성 검증", fn)

    # ── RESULTS 정의 무결성 ───────────────────────────────────────
    def test_results_schema(self):
        def fn():
            required = {'type', 'badge_class', 'icon', 'title', 'description'}
            for rkey, res in RESULTS.items():
                missing = required - set(res.keys())
                assert not missing, f"{rkey} 에 누락된 키: {missing}"
        self._run("RESULTS 딕셔너리 스키마 무결성 검증", fn)

    def run_all(self):
        self.test_listed_yes()
        self.test_isms_yes()
        self.test_not_icsp()
        self.test_revenue_yes()
        self.test_users_yes()
        self.test_special_industry()
        self.test_all_no()
        self.test_icsp_yes_goto_step4()
        self.test_revenue_no_goto_step5()
        self.test_users_no_goto_step6()
        self.test_special_industry_not_reached_if_mandatory()
        self.test_steps_schema()
        self.test_results_schema()


# ============================================================
# 통합 테스트: HTTP 요청으로 실제 라우트 검증
# ============================================================

class CheckerIntegrationTests:
    def __init__(self):
        self.results: list[UnitTestResult] = []
        self.session = requests.Session()

    def _run(self, name, func):
        r = UnitTestResult(name)
        r.start()
        try:
            func()
            r.finish(TestStatus.PASSED)
        except AssertionError as e:
            r.finish(TestStatus.FAILED, str(e))
        except Exception as e:
            r.finish(TestStatus.FAILED, f"예외: {e}")
        self.results.append(r)

    def _reset(self):
        """세션 초기화 (GET /checker)"""
        self.session = requests.Session()
        res = self.session.get(f"{BASE_URL}/checker", allow_redirects=True)
        assert res.status_code == 200, f"체커 접근 실패: {res.status_code}"

    def _post_step(self, step_id, answer):
        """단계 답변 POST"""
        return self.session.post(
            f"{BASE_URL}/checker/step",
            data={'step_id': step_id, 'answer': answer},
            allow_redirects=True
        )

    def test_checker_accessible_without_login(self):
        def fn():
            res = requests.get(f"{BASE_URL}/checker")
            assert res.status_code == 200, f"비로그인 접근 실패: {res.status_code}"
            assert "정보보호공시" in res.text, "페이지 내용 확인 실패"
        self._run("비로그인 상태에서 /checker 접근 가능 여부", fn)

    def test_flow_listed_yes(self):
        def fn():
            self._reset()
            res = self._post_step('step1', 'YES')
            assert res.status_code == 200
            assert "MANDATORY_2027" in res.url or "의무 공시 대상" in res.text, \
                "상장=YES 후 의무 결과 미확인"
        self._run("[HTTP] step1 상장=YES → 결과 페이지 의무 확정", fn)

    def test_flow_isms_yes(self):
        def fn():
            self._reset()
            self._post_step('step1', 'NO')
            res = self._post_step('step2', 'YES')
            assert res.status_code == 200
            assert "의무 공시 대상" in res.text, "ISMS=YES 후 의무 결과 미확인"
        self._run("[HTTP] step2 ISMS=YES → 결과 페이지 의무 확정", fn)

    def test_flow_not_icsp(self):
        def fn():
            self._reset()
            self._post_step('step1', 'NO')
            self._post_step('step2', 'NO')
            res = self._post_step('step3', 'NO')
            assert res.status_code == 200
            assert "의무 공시 대상" not in res.text or "현재 의무 공시 대상이 아닙니다" in res.text, \
                "정보통신서비스 NO 후 자율 결과 미확인"
        self._run("[HTTP] step3 정보통신서비스=NO → 자율 결과 종료", fn)

    def test_flow_all_no_voluntary(self):
        def fn():
            self._reset()
            for sid, ans in [('step1','NO'),('step2','NO'),('step3','YES'),
                              ('step4','NO'),('step5','NO'),('step6','NO')]:
                res = self._post_step(sid, ans)
            assert res.status_code == 200
            assert "현재 의무 공시 대상이 아닙니다" in res.text or "자율" in res.text, \
                "전 기준 NO 후 자율 결과 미확인"
        self._run("[HTTP] 전 기준 NO → VOLUNTARY 결과 확인", fn)

    def test_flow_special_industry(self):
        def fn():
            self._reset()
            for sid, ans in [('step1','NO'),('step2','NO'),('step3','YES'),
                              ('step4','NO'),('step5','NO'),('step6','YES')]:
                res = self._post_step(sid, ans)
            assert res.status_code == 200
            assert "별도 규제" in res.text or "특수" in res.text, \
                "특수업종=YES 후 SPECIAL_INDUSTRY 결과 미확인"
        self._run("[HTTP] step6 특수업종=YES → SPECIAL_INDUSTRY 결과 확인", fn)

    def test_result_page_has_kisa_link(self):
        def fn():
            self._reset()
            self._post_step('step1', 'YES')
            res = self.session.get(f"{BASE_URL}/checker/result")
            assert "isds.kisa.or.kr" in res.text, "KISA 링크 미존재"
        self._run("[HTTP] 결과 페이지에 KISA 공식 포털 링크 존재 확인", fn)

    def test_invalid_step_redirects(self):
        def fn():
            self._reset()
            res = self.session.post(
                f"{BASE_URL}/checker/step",
                data={'step_id': '', 'answer': ''},
                allow_redirects=True
            )
            assert res.status_code == 200
            assert "/checker" in res.url or "공시 대상 확인" in res.text, \
                "잘못된 입력 시 체커 시작으로 리다이렉트 안 됨"
        self._run("[HTTP] 빈 step_id/answer 입력 시 안전하게 처리", fn)

    def test_result_without_session_redirects(self):
        def fn():
            # 세션 없이 결과 페이지 직접 접근
            res = requests.get(f"{BASE_URL}/checker/result", allow_redirects=True)
            assert res.status_code == 200
            assert "/checker" in res.url or "공시 대상 확인" in res.text, \
                "세션 없는 결과 접근 시 체커 시작으로 리다이렉트 안 됨"
        self._run("[HTTP] 세션 없이 /checker/result 직접 접근 시 리다이렉트", fn)

    def run_all(self):
        self.test_checker_accessible_without_login()
        self.test_flow_listed_yes()
        self.test_flow_isms_yes()
        self.test_flow_not_icsp()
        self.test_flow_all_no_voluntary()
        self.test_flow_special_industry()
        self.test_result_page_has_kisa_link()
        self.test_invalid_step_redirects()
        self.test_result_without_session_redirects()


# ============================================================
# 결과 출력
# ============================================================

def print_results(title, results):
    print(f"\n{'='*W}")
    print(f"  {title}")
    print(f"{'='*W}")
    passed = failed = 0
    for r in results:
        icon = r.status.value if r.status else "?"
        elapsed = f"{r.elapsed_ms:.0f}ms" if r.elapsed_ms else "-"
        print(f"  {icon}  {r.name:<50} {elapsed:>8}")
        if r.status == TestStatus.FAILED and r.message:
            print(f"       └─ {r.message}")
        if r.status == TestStatus.PASSED:
            passed += 1
        elif r.status == TestStatus.FAILED:
            failed += 1
    print(f"{'─'*W}")
    print(f"  결과: PASSED {passed} / FAILED {failed} / 총 {passed+failed}")
    return failed


def main():
    print(f"\n{'='*W}")
    print(f"  정보보호공시 대상 판별 체커 테스트")
    print(f"  실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*W}")

    # 단위 테스트 (Flask 서버 불필요)
    unit = CheckerUnitTests()
    unit.run_all()
    unit_fail = print_results("단위 테스트: _decide_next 판별 로직", unit.results)

    # 통합 테스트 (Flask 서버 필요)
    print(f"\n통합 테스트를 위해 Flask 서버({BASE_URL}) 연결 확인 중...")
    try:
        requests.get(BASE_URL, timeout=3)
        integration = CheckerIntegrationTests()
        integration.run_all()
        integ_fail = print_results("통합 테스트: HTTP 라우트 검증", integration.results)
    except Exception:
        print(f"  ⚠️  서버 미응답 — 통합 테스트 건너뜀 (서버 실행 후 재시도)")
        integ_fail = 0

    total_fail = unit_fail + integ_fail
    print(f"\n{'='*W}")
    if total_fail == 0:
        print("  ✅  전체 테스트 PASSED")
    else:
        print(f"  ❌  {total_fail}개 실패 — 위 내용 확인 필요")
    print(f"{'='*W}\n")
    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
