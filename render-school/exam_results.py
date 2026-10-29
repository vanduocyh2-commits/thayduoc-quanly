"""Keep the best exam result while retaining a compact score ledger for every attempt."""
import copy
import math

DETAIL_FIELDS = ('answers', 'text', 'attachments', 'score', 'feedback', 'quizScore', 'examCode',
                 'attemptCount', 'submittedAt', 'gradedAt', 'gradedBy', 'summaryOnly')


def valid_score(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 10


def attempt_number(value, fallback=1):
    return value if type(value) is int and value >= 1 else fallback


def result_attempts(data, submitted_at):
    attempts = {}
    sources = [dict(data, submittedAt=submitted_at)]
    sources += list(reversed(data.get('history', [])))
    if isinstance(data.get('bestAttempt'), dict):
        sources.append(data['bestAttempt'])
    sources += [dict(row, summaryOnly=True) for row in data.get('attemptScores', []) if isinstance(row, dict)]
    for source in sources:
        number = attempt_number(source.get('attemptCount'))
        if number in attempts:
            continue
        row = {key: copy.deepcopy(source[key]) for key in DETAIL_FIELDS if key in source}
        row.update(attemptCount=number, submittedAt=source.get('submittedAt') or submitted_at)
        row['score'] = row.get('score') if valid_score(row.get('score')) else None
        attempts[number] = row
    return attempts


def with_best_result(data, submitted_at):
    attempts = result_attempts(data, submitted_at)
    data['attemptScores'] = [
        {key: row.get(key) for key in ('attemptCount', 'score', 'submittedAt', 'gradedAt')}
        for _, row in sorted(attempts.items())
    ]
    scored = [row for row in attempts.values() if valid_score(row.get('score'))]
    best = max(scored, key=lambda row: (row['score'], -row['attemptCount'])) if scored else None
    data['bestScore'] = best['score'] if best else None
    data['bestAttemptCount'] = best['attemptCount'] if best else None
    data['bestSubmittedAt'] = best['submittedAt'] if best else None
    data['bestAttempt'] = copy.deepcopy(best)
    return data


def grade_attempt(data, submitted_at, number, score, feedback, graded_at, graded_by):
    number = attempt_number(number, 0)
    attempts = result_attempts(data, submitted_at)
    if number not in attempts:
        raise ValueError('Không tìm thấy lần làm bài cần chấm.')
    replacement = dict(score=score, feedback=feedback, gradedAt=graded_at, gradedBy=graded_by)
    if number == attempt_number(data.get('attemptCount')):
        data.update(replacement)
    else:
        for row in data.get('history', []):
            if row.get('attemptCount') == number:
                row.update(replacement)
        if isinstance(data.get('bestAttempt'), dict) and data['bestAttempt'].get('attemptCount') == number:
            data['bestAttempt'].update(replacement)
        for row in data.get('attemptScores', []):
            if row.get('attemptCount') == number:
                row.update(replacement)
    return with_best_result(data, submitted_at)
