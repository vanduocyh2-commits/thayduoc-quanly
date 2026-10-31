import io
import pytest
from openpyxl import Workbook
from answer_keys import read_answer_keys


def excel(rows):
    workbook = Workbook()
    for row in rows:
        workbook.active.append(row)
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def matrix():
    return [['Câu\\Mã Đề', 101, '0102'], ['1', 'B', 'C'], [2, 'D', 'A'],
            [1, 'ĐĐSS', 'SĐSĐ'], [1, '0,25', '0123'], [2, 0, -2.5]]


def test_tn_maker_sections_codes_and_numeric_answers():
    rows = read_answer_keys(excel(matrix()))
    assert len(rows) == 10
    by_key = {(r['code'], r['type'], r['number']): r['answer'] for r in rows}
    assert by_key['101', 'quiz', 1] == 'B'
    assert by_key['0102', 'quiz', 1] == 'C'
    assert by_key['101', 'truefalse', 1] == 'Đ Đ S S'
    assert by_key['0102', 'truefalse', 1] == 'S Đ S Đ'
    assert by_key['101', 'short', 1] == '0,25'
    assert by_key['0102', 'short', 1] == '0123'
    assert by_key['101', 'short', 2] == '0'
    assert by_key['0102', 'short', 2] == '-2.5'


@pytest.mark.parametrize('rows', [
    [], [['Câu\\Mã Đề', '101']],
    [['Câu\\Mã Đề', '101', '101'], [1, 'A', 'B']],
    [['Câu\\Mã Đề', '101', None], [1, 'A', 'B']],
    [['Câu\\Mã Đề', '101'], [1, 'A'], [3, 'B']],
    [['Câu\\Mã Đề', '101'], [1, 'A'], [2, None]],
    [['Câu\\Mã Đề', '101'], [1, 'A'], [2, 'E']],
    [['Câu\\Mã Đề', '101'], [1, 'ĐĐSS'], [2, 'ĐSS']],
    [['Câu\\Mã Đề', '101'], [1, 'A'], [1, 'B']],
    [['Câu\\Mã Đề', '101'], [1, 'A', 'B']],
])
def test_invalid_matrices_are_rejected(rows):
    with pytest.raises(ValueError):
        read_answer_keys(excel(rows))


def test_legacy_rows_still_import():
    assert read_answer_keys(excel([
        ['Ma de', 'Dang', 'Cau', 'Dap an'], ['101', 'short', 1, '0,25']
    ])) == [dict(code='101', type='short', number=1, answer='0,25')]
