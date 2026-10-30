"""Grade-safe updates to shared exam sources and existing attempts."""
import copy
from exam_results import result_attempts,with_best_result,valid_score

def class_grade(course):
 import re,unicodedata
 value=str(course.get('grade') or '')
 if value.isdigit() and 1<=int(value)<=12:return str(int(value))
 name=''.join(c for c in unicodedata.normalize('NFD',course.get('name','')) if not unicodedata.combining(c)).lower()
 match=re.search(r'(?:^|\s)(?:lop\s*|khoi\s*)?(1[0-2]|[1-9])(?=[a-z]|\b)',name)
 return match[1] if match else ''
def matches_grade(exam,course):
 grade=str(exam.get('grade') or '');target=class_grade(course)
 return not grade or bool(target) and grade==target

def code_exam(exam,code):
 return next((v for v in exam.get('variants',[]) if v['code']==code),exam)
def check_update(old,new,used):
 if not used:return
 old_codes={v['code'] for v in old.get('variants',[])};new_codes={v['code'] for v in new.get('variants',[])}
 if old_codes!=new_codes:raise ValueError('Đã có bài làm: giữ nguyên các mã đề.')
 for code in old_codes or {''}:
  a=code_exam(old,code);b=code_exam(new,code)
  for field in ['questions','essays']:
   before=a.get(field,[]);after=b.get(field,[])
   if len(before)!=len(after) or any(q.get('type','quiz')!=r.get('type','quiz') or q.get('points')!=r.get('points') for q,r in zip(before,after)):raise ValueError('Đã có bài làm: giữ số câu, loại câu và điểm từng câu để bảo toàn bài tự luận.')

def regrade_submission(data,created_at,old,new,score_questions):
 data=copy.deepcopy(data);attempts=result_attempts(data,created_at)
 for number,row in attempts.items():
  mode=new.get('gradingMode','auto')
  if new['type']=='essay' or mode=='manual':continue
  if row.get('summaryOnly') and 'answers' not in row:raise ValueError('Có lần làm cũ chỉ còn điểm tổng kết, không còn câu trả lời để chấm lại. Chưa cập nhật để giữ nguyên điểm cũ.')
  variant=code_exam(new,row.get('examCode',''));earned=score_questions(new,variant,row.get('answers'))
  previous_quiz=row.get('quizScore')
  if mode=='semi':
   if new['type']=='mixed' and valid_score(row.get('score')) and valid_score(previous_quiz):row['essayScore']=max(0,row['score']-previous_quiz)
   row.update(quizScore=earned,score=None)
  elif new['type']=='quiz':row['score']=earned
  else:
   row['quizScore']=earned
   if valid_score(row.get('score')) and valid_score(previous_quiz):row['score']=round(max(0,min(10,earned+max(0,row['score']-previous_quiz))),2)
  row['regraded']=True
 latest=data.get('attemptCount',1);data.update(attempts[latest])
 data['history']=[attempts.get(row.get('attemptCount',1),row) for row in data.get('history',[])]
 old_best=data.get('bestAttempt')
 if old_best:data['bestAttempt']=attempts.get(old_best.get('attemptCount',1),old_best)
 data['attemptScores']=[{k:row.get(k) for k in ['attemptCount','score','submittedAt','gradedAt']} for row in attempts.values()]
 return with_best_result(data,created_at)
