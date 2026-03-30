"""
infosd - 정보보호공시 의무 대상 여부 판별 라우팅
로그인 불필요 (공개 접근)
2027년 이후 확대 기준 적용 / 6단계 종합 판별
"""
from flask import Blueprint, render_template, request, redirect, url_for, session

bp_checker = Blueprint('checker', __name__, url_prefix='/checker')

# ============================================================
# 단계 정의
# ============================================================

STEPS = {
    'step1': {
        'id': 'step1',
        'title': '상장 법인 여부',
        'question': '귀사는 코스피(KOSPI) 또는 코스닥(KOSDAQ) 상장 법인입니까?',
        'hint': (
            '2027년부터 코스피·코스닥 상장 법인 전체가 의무 공시 대상으로 확대됩니다.\n'
            '매출액·이용자 수 기준과 무관하게 상장 사실만으로 의무 대상이 됩니다.'
        ),
        'choices': [
            {'value': 'YES', 'label': '예 (코스피 또는 코스닥 상장)'},
            {'value': 'NO',  'label': '아니오 (비상장)'},
        ],
        'progress_max': 6,
    },
    'step2': {
        'id': 'step2',
        'title': 'ISMS / ISMS-P 인증 보유 여부',
        'question': '귀사는 현재 정보보호관리체계(ISMS 또는 ISMS-P) 인증을 보유하고 있습니까?',
        'hint': (
            '과학기술정보통신부 고시 기준 인증입니다.\n'
            '· ISMS: 정보보호 관리체계 인증\n'
            '· ISMS-P: 개인정보보호 포함 통합 인증\n\n'
            '2027년부터 인증 보유 기업 전체가 의무 공시 대상에 포함됩니다.\n'
            '※ 인증 의무 대상(매출 100억 이상 + 이용자 100만 이상 등)이지만 아직 미취득 상태라면 '
            '"아니오"를 선택하되, 인증 취득 시 즉시 공시 의무가 발생합니다.'
        ),
        'choices': [
            {'value': 'YES', 'label': '예 (ISMS 또는 ISMS-P 인증 보유 중)'},
            {'value': 'NO',  'label': '아니오 (미보유)'},
        ],
        'progress_max': 6,
    },
    'step3': {
        'id': 'step3',
        'title': '정보통신서비스 제공 여부',
        'question': '귀사는 인터넷을 통해 외부 이용자에게 서비스나 정보를 제공합니까?',
        'hint': (
            '아래에 해당하면 "예"입니다.\n'
            '· 온라인 쇼핑몰, 앱, 플랫폼, 포털, SaaS, 게임, 핀테크 서비스\n'
            '· 채용 사이트 (불특정 구직자 대상 — 정보통신서비스에 해당)\n'
            '· 거래처 포털 (B2B라도 인터넷을 통한 정보 매개 — 해당)\n'
            '· 고객 대상 홈페이지, 회원 가입·로그인 기능이 있는 웹사이트'
        ),
        'choices': [
            {'value': 'YES', 'label': '예 (외부 이용자 대상 온라인 서비스·사이트 운영)'},
            {'value': 'NO',  'label': '아니오 (인터넷을 통한 외부 서비스 없음)'},
        ],
        'progress_max': 6,
    },
    'step4': {
        'id': 'step4',
        'title': '정보통신서비스 매출액 기준',
        'question': '전년도 정보통신서비스 관련 매출액이 3,000억 원 이상입니까?',
        'hint': (
            '전체 매출액이 아닌 "정보통신서비스 관련 매출액" 기준입니다.\n'
            '· 해당: 온라인 판매, 구독료, 광고 수익, 앱 내 결제, 플랫폼 수수료 등\n'
            '· 오프라인 매출 및 정보통신서비스와 무관한 매출은 제외됩니다.\n'
            '기준 연도: 공시 연도의 전년도 (예: 2027년 공시 → 2026년 실적)'
        ),
        'choices': [
            {'value': 'YES', 'label': '예 (3,000억 원 이상)'},
            {'value': 'NO',  'label': '아니오 (3,000억 원 미만)'},
        ],
        'progress_max': 6,
    },
    'step5': {
        'id': 'step5',
        'title': '일일 평균 이용자 수 기준',
        'question': '전년도 기준 서비스 일일 평균 이용자 수가 100만 명 이상입니까?',
        'hint': (
            '산정 기준: 전년도 1월 1일~12월 31일 전체의 일일 평균 이용자 수\n'
            '(구 기준인 "전년도 말 직전 3개월 평균"에서 변경됨)\n\n'
            '· "이용자"는 서비스에 실제로 접속·이용한 사람 기준입니다.\n'
            '· 회원 수(가입자 수)가 아닌 실이용자(DAU 개념) 기준입니다.\n'
            '· 복수 서비스 운영 시 각 서비스별로 별도 산정합니다.'
        ),
        'choices': [
            {'value': 'YES', 'label': '예 (100만 명 이상)'},
            {'value': 'NO',  'label': '아니오 (100만 명 미만)'},
        ],
        'progress_max': 6,
    },
    'step6': {
        'id': 'step6',
        'title': '특수 업종 해당 여부',
        'question': '귀사는 아래 업종에 해당합니까?',
        'hint': (
            '· 금융회사 (은행, 보험, 증권, 카드 등)\n'
            '· 전자금융사업자 (간편결제, 가상자산 등)\n'
            '· 의료기관 (병원, 학교병원, 요양원 등)\n'
            '· 공공기관 (국가·지자체·공기업 등)\n\n'
            '※ 이 업종들은 금융보안원·개인정보보호위원회 등 별도 규제기관의 정보보호 의무도 병존합니다.\n'
            '2027년부터는 이 업종들도 정보보호공시 의무 대상에 포함됩니다.'
        ),
        'choices': [
            {'value': 'YES', 'label': '예 (금융·전자금융·의료·공공기관 해당)'},
            {'value': 'NO',  'label': '아니오 (해당 없음)'},
        ],
        'progress_max': 6,
    },
}

# ============================================================
# 결과 정의
# ============================================================

RESULTS = {
    'MANDATORY_2027': {
        'type': 'MANDATORY_2027',
        'badge_class': 'danger',
        'icon': 'bi-exclamation-circle-fill',
        'title': '의무 공시 대상입니다 (2027년부터)',
        'description': '귀사는 2027년부터 정보보호공시 의무 대상에 해당합니다. 해당 연도부터 매년 6월 30일까지 공시를 완료해야 합니다.',
    },
    'MANDATORY': {
        'type': 'MANDATORY',
        'badge_class': 'danger',
        'icon': 'bi-exclamation-circle-fill',
        'title': '의무 공시 대상입니다',
        'description': '귀사는 정보보호공시 의무 대상에 해당합니다. 매년 6월 30일까지 공시를 완료해야 합니다.',
    },
    'VOLUNTARY': {
        'type': 'VOLUNTARY',
        'badge_class': 'warning',
        'icon': 'bi-info-circle-fill',
        'title': '현재 의무 공시 대상이 아닙니다',
        'description': '현재 기준으로 의무 공시 대상에 해당하지 않습니다. 단, 자율적으로 공시를 진행할 수 있으며, 향후 기준 변경 시 재확인이 필요합니다.',
    },
    'SPECIAL_INDUSTRY': {
        'type': 'SPECIAL_INDUSTRY',
        'badge_class': 'warning',
        'icon': 'bi-building-check',
        'title': '별도 규제 체계 적용 업종입니다',
        'description': '귀사가 속한 업종(금융·전자금융·의료·공공기관)은 별도 법령에 따른 정보보호 의무가 적용됩니다. 2027년부터는 정보보호공시 의무도 추가됩니다. 소관 규제기관 및 전문가 확인을 권장합니다.',
    },
}

# ============================================================
# 헬퍼 함수
# ============================================================

STEP_ORDER = ['step1', 'step2', 'step3', 'step4', 'step5', 'step6']
# step1: 상장 여부 / step2: ISMS / step3: 정보통신서비스 여부 / step4: 매출액 / step5: 이용자수 / step6: 특수업종


def _get_step_progress(step_id):
    """현재 단계 번호 반환 (1부터 시작)"""
    if step_id in STEP_ORDER:
        return STEP_ORDER.index(step_id) + 1
    return 1


def _get_history_answer(history, step_id):
    """이력에서 특정 step의 답변 반환"""
    for h in history:
        if h['step'] == step_id:
            return h['answer']
    return None


def _decide_next(step_id, answer, history):
    """
    현재 step, 답변, 이력을 기반으로 다음 step 또는 result를 반환.
    반환값: ('step', step_id) 또는 ('result', result_key, reason)
    """
    if step_id == 'step1':
        if answer == 'YES':
            return ('result', 'MANDATORY_2027',
                    '코스피 또는 코스닥 상장 법인으로, 2027년부터 의무 공시 대상에 해당합니다.')
        return ('step', 'step2')

    elif step_id == 'step2':
        if answer == 'YES':
            return ('result', 'MANDATORY_2027',
                    'ISMS 또는 ISMS-P 인증 보유 기업으로, 2027년부터 의무 공시 대상에 해당합니다.')
        return ('step', 'step3')

    elif step_id == 'step3':
        if answer == 'YES':
            return ('step', 'step4')
        else:
            # 정보통신서비스 미제공 → 매출액·이용자 수 기준 자체가 적용 안 됨
            return ('result', 'VOLUNTARY',
                    '정보통신서비스 제공자에 해당하지 않아 매출액·이용자 수 기준이 적용되지 않습니다. 현재 의무 공시 대상이 아닙니다.')

    elif step_id == 'step4':
        if answer == 'YES':
            return ('result', 'MANDATORY',
                    '전년도 정보통신서비스 관련 매출액이 3,000억 원 이상으로 의무 공시 대상입니다.')
        return ('step', 'step5')

    elif step_id == 'step5':
        if answer == 'YES':
            return ('result', 'MANDATORY',
                    '전년도 서비스 일일 평균 이용자 수가 100만 명 이상으로 의무 공시 대상입니다.')
        # 매출액·이용자 수 모두 기준 미달 → 특수업종 여부 확인
        return ('step', 'step6')

    elif step_id == 'step6':
        if answer == 'YES':
            return ('result', 'SPECIAL_INDUSTRY',
                    '현재 기준의 매출액·이용자 수는 해당 없으나, 귀사의 업종(금융·전자금융·의료·공공기관)은 별도 규제 체계가 적용됩니다.')
        return ('result', 'VOLUNTARY',
                '상장 법인, ISMS 인증, 매출액(3,000억), 이용자 수(100만) 기준을 모두 충족하지 않아 현재 의무 공시 대상이 아닙니다.')

    return ('result', 'VOLUNTARY', '판별 기준에 해당하지 않습니다.')


# ============================================================
# 라우트
# ============================================================

@bp_checker.route('', methods=['GET'])
def main():
    """
    공시 대상 여부 판별 체커 시작 페이지.
    세션을 초기화하고 첫 번째 단계(step1)를 표시한다.
    """
    session['checker_steps'] = []
    return render_template(
        'checker/main.html',
        step=STEPS['step1'],
        progress_num=1,
    )


@bp_checker.route('/step', methods=['POST'])
def step():
    """
    단계별 답변을 처리하고 다음 단계 또는 결과 페이지로 이동한다.
    세션의 checker_steps 리스트에 step/answer 이력을 저장한다.
    DB 저장 없이 세션만 사용한다.
    """
    current_step_id = request.form.get('step_id', '').strip()
    answer = request.form.get('answer', '').strip()

    if not current_step_id or not answer:
        return redirect(url_for('checker.main'))

    # 이력 저장 (동일 step 재답변 시 이후 이력 제거)
    history = session.get('checker_steps', [])
    history = [h for h in history if h['step'] != current_step_id]
    step_def = STEPS.get(current_step_id)
    answer_label = answer
    if step_def:
        for ch in step_def.get('choices', []):
            if ch['value'] == answer:
                answer_label = ch['label']
                break
    history.append({
        'step': current_step_id,
        'question': step_def['question'] if step_def else current_step_id,
        'answer': answer,
        'answer_label': answer_label,
    })
    session['checker_steps'] = history

    # 다음 단계 결정
    decision = _decide_next(current_step_id, answer, history)

    if decision[0] == 'step':
        next_step_id = decision[1]
        next_step = STEPS.get(next_step_id)
        if not next_step:
            return redirect(url_for('checker.main'))
        return render_template(
            'checker/main.html',
            step=next_step,
            progress_num=_get_step_progress(next_step_id),
        )
    else:
        _, result_key, reason = decision
        session['checker_result'] = result_key
        session['checker_reason'] = reason
        return redirect(url_for('checker.result'))


@bp_checker.route('/result', methods=['GET'])
def result():
    """
    최종 판별 결과 페이지.
    세션에 저장된 result_key와 이력을 바탕으로 결과를 표시한다.
    """
    result_key = session.get('checker_result')
    reason = session.get('checker_reason', '')
    history = session.get('checker_steps', [])

    if not result_key or result_key not in RESULTS:
        return redirect(url_for('checker.main'))

    return render_template(
        'checker/result.html',
        result=RESULTS[result_key],
        reason=reason,
        history=history,
    )
