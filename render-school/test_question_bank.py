import copy
from test_school import action,state
from test_school_bank import prepare,update

def question(text='Tính 1 + 1',curriculum='GDPT 2018'):
 return {
  'type':'quiz','text':text,'answers':['0','1','2','3'],'correct':2,
  'points':10,'topic':'Phép cộng','level':'Nhận biết','outcome':'Tính được tổng hai số tự nhiên.',
  'grade':'10','subject':'Toán','curriculum':curriculum,'textbook':'Kết nối tri thức với cuộc sống',
  'chapter':'Chương I','chapterOrder':1,'lesson':'Bài 1','lessonOrder':1
 }

def create_classified_exam(client,cid,title,bank_only=True,questions=None):
 data={
  'title':title,'body':'Bài kiểm tra','grade':'10','type':'quiz','composed':True,
  'questionBankVersion':1,'bankOnly':bank_only,'gradingMode':'auto','maxAttempts':0,
  'questions':questions or [question()],'essays':[]
 }
 result=action(client,{'action':'record','kind':'assignment','courseId':cid,'data':data})
 assert result.status_code==200,result.json
 return next(row for row in state(client)['library'] if row['data']['title']==title)

def bank_rows(client):
 return state(client).get('questionBank',[])

def test_school_question_bank_classification_dedup_and_snapshot_isolation(client,app):
 t1,t2,pupil,cs,ms=prepare(client,app)

 original=create_classified_exam(t1,cs['10A'],'Đề nguồn',bank_only=True)
 assert len(bank_rows(t1))==1
 saved=bank_rows(t1)[0]
 assert saved['data']['grade']=='10'
 assert saved['data']['subject']=='Toán'
 assert saved['data']['curriculum']=='GDPT 2018'
 assert saved['data']['chapter']=='Chương I'
 assert saved['data']['lesson']=='Bài 1'
 assert saved['data']['level']=='Nhận biết'
 assert saved['author_id']==ms['teach1']
 assert not [row for row in state(t1)['records'] if row['kind']=='questionBank']

 # A different teacher reuses the same question in another class: no duplicate is created.
 reused=create_classified_exam(t2,cs['10B'],'Đề tái sử dụng',bank_only=False)
 assert len(bank_rows(t1))==1
 assert len(bank_rows(t2))==1
 assert bank_rows(t2)[0]['id']==saved['id']
 assert bank_rows(t2)[0]['author_id']==ms['teach1']

 # Students may see the assigned question statement, but never the question bank or its key.
 pupil_state=state(pupil)
 assert pupil_state.get('questionBank')==[]
 delivered=next(row for row in pupil_state['records'] if row['id']==reused['id'])
 assert 'correct' not in delivered['data']['questions'][0]

 # Updating the source bank question does not mutate a separately saved exam snapshot.
 changed=copy.deepcopy(original['data'])
 changed['questions'][0]['text']='Tính 2 + 2'
 result=update(t1,original,changed)
 assert result.status_code==200,result.json
 assert bank_rows(t1)[0]['data']['text']=='Tính 2 + 2'
 still_saved=next(row for row in state(t2)['library'] if row['id']==reused['id'])
 assert still_saved['data']['questions'][0]['text']=='Tính 1 + 1'

 # A teacher cannot overwrite another author's bank record by passing its ID.
 altered=copy.deepcopy(reused['data'])
 altered['questions'][0]['text']='Câu hỏi được sửa bởi giáo viên khác'
 result=update(t2,reused,altered)
 assert result.status_code==200,result.json
 rows=bank_rows(t1)
 source=next(row for row in rows if row['id']==saved['id'])
 assert source['data']['text']=='Tính 2 + 2'
 assert any(row['author_id']==ms['teach2'] and row['data']['text']=='Câu hỏi được sửa bởi giáo viên khác' for row in rows)

def test_school_question_bank_keeps_program_as_part_of_dedup_key(client,app):
 t1,t2,pupil,cs,ms=prepare(client,app)
 create_classified_exam(t1,cs['10A'],'Đề GDPT 2018',bank_only=True,questions=[question(curriculum='GDPT 2018')])
 create_classified_exam(t1,cs['10A'],'Đề chương trình khác',bank_only=True,questions=[question(curriculum='Chương trình thử nghiệm')])
 programs={row['data']['curriculum'] for row in bank_rows(t1)}
 assert programs=={'GDPT 2018','Chương trình thử nghiệm'}
