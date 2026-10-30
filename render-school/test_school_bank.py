import json,io,copy
from test_school import app,client,action,setup,state,login,token

def prepare(admin,app):
 setup(admin)
 for user,role in [('teach1','teacher'),('teach2','teacher'),('pupil','student')]:assert action(admin,{'action':'member','username':user,'name':user,'role':role,'password':'Password123!'}).status_code==200
 ms={m['username']:m['id'] for m in state(admin)['members']}
 for name,teacher in [('10A','teach1'),('10B','teach2'),('11C','teach2')]:assert action(admin,{'action':'course','name':name,'subject':'Toán','teacherId':ms[teacher]}).status_code==200
 cs={c['name']:c['id'] for c in state(admin)['courses']}
 assert action(admin,{'action':'enroll','courseId':cs['10B'],'memberId':ms['pupil']}).status_code==200
 clients=[app.test_client() for _ in range(3)]
 for c,u in zip(clients,['teach1','teach2','pupil']):assert login(c,u).status_code==200
 return *clients,cs,ms

def create_exam(t,cid,mode='auto',bank=True):
 data={'title':'Đề gốc','body':'Đọc đề','grade':'10','type':'mixed','composed':True,'bankOnly':bank,'gradingMode':mode,'maxAttempts':0,'questions':[{'text':'1+1','answers':['1','2','3','4'],'correct':1,'points':4,'topic':'Số','level':'Nhận biết','type':'quiz'}],'essays':[{'text':'Giải thích','points':6,'topic':'Số','level':'Vận dụng','type':'essay'}]}
 r=action(t,{'action':'record','kind':'assignment','courseId':cid,'data':data});assert r.status_code==200,r.json
 return next(r for r in state(t)['library'] if r['data']['title']=='Đề gốc')

def update(t,record,data=None):
 return t.post('/api/exams/'+record['id']+'/update',data={'data':json.dumps(data or record['data']),'expectedUpdatedAt':record['data'].get('updatedAt') or record['created_at']},headers={'Origin':'http://localhost','X-CSRF-Token':token(t)})

def test_shared_bank_assignment_author_update_regrade_and_archive(client,app):
 t1,t2,pupil,cs,ms=prepare(client,app);root=create_exam(t1,cs['10A'])
 assert root['id'] in [r['id'] for r in state(t2)['library']]
 assert not [r for r in state(t1)['records'] if r['kind']=='assignment']
 assert action(pupil,{'action':'submit','assignmentId':root['id'],'answers':[1],'text':'proof'}).status_code==403
 assert action(t2,{'action':'assignBankExam','id':root['id'],'courseId':cs['11C']}).status_code==400
 assert action(t2,{'action':'assignBankExam','id':root['id'],'courseId':cs['10B'],'maxAttempts':0}).status_code==200
 delivered=next(r for r in state(pupil)['records'] if r['kind']=='assignment')
 assert not delivered['data'].get('bankOnly') and 'correct' not in delivered['data']['questions'][0]
 assert action(pupil,{'action':'submit','assignmentId':delivered['id'],'answers':[1],'text':'proof'}).status_code==200
 sub=state(t2)['submissions'][0]
 assert action(t2,{'action':'grade','id':sub['id'],'score':7,'feedback':'Tự luận 3 điểm'}).status_code==200
 assert update(t2,root).status_code==403
 data=copy.deepcopy(root['data']);data['questions'][0]['correct']=0;data['title']='Đề đã sửa'
 result=update(t1,root,data);assert result.status_code==200,result.json
 assert result.json['regradedSubmissions']==1
 revised=state(pupil)['submissions'][0]['data'];assert revised['score']==3 and revised['bestScore']==3
 copied=next(r for r in state(pupil)['records'] if r['id']==delivered['id']);assert copied['data']['title']=='Đề đã sửa'
 assert copied['data']['createdAt']==delivered['data']['createdAt'] and copied['data']['updatedAt']!=delivered['data']['updatedAt']
 assert update(t1,root,data).status_code==409
 assert action(t2,{'action':'archiveBankExam','id':root['id']}).status_code==403
 assert action(t1,{'action':'archiveBankExam','id':root['id']}).status_code==200
 assert root['id'] not in [r['id'] for r in state(t2)['library']]
 assert next(r for r in state(pupil)['records'] if r['id']==delivered['id'])
 assert state(pupil)['submissions'][0]['data']['score']==3

def test_semi_and_manual_grade_require_teacher_and_preserve_proposal(client,app):
 t1,t2,pupil,cs,ms=prepare(client,app)
 for mode in ['semi','manual']:
  root=create_exam(t1,cs['10A'],mode=mode)
  assert action(t1,{'action':'assignBankExam','id':root['id'],'courseId':cs['10B'],'gradingMode':mode}).status_code==200
  delivered=next(r for r in state(pupil)['records'] if r['kind']=='assignment' and r['data']['gradingMode']==mode)
  assert action(pupil,{'action':'submit','assignmentId':delivered['id'],'answers':[1],'text':'essay'}).status_code==200
  sub=next(s for s in state(t1)['submissions'] if s['assignment_id']==delivered['id'])
  assert sub['data']['score'] is None
  if mode=='semi':assert sub['data']['quizScore']==4
  else:assert 'quizScore' not in sub['data']
  assert action(t1,{'action':'grade','id':sub['id'],'score':8}).status_code==200
  assert next(s for s in state(pupil)['submissions'] if s['id']==sub['id'])['data']['score']==8

def test_grade_filter_file_copy_and_replacement_author_only(client,app):
 t1,t2,pupil,cs,ms=prepare(client,app)
 # Published exam documents are shared across teachers, but student grade checks apply to downloads too.
 fields={'courseId':cs['10B'],'title':'PDF bank','category':'exam','grade':'10','body':'essay','published':'true','file':(io.BytesIO(b'%PDF-1.4\nold\n%%EOF'),'de.pdf')}
 r=t2.post('/api/library',data=fields,headers={'Origin':'http://localhost','X-CSRF-Token':token(t2)});assert r.status_code==200
 root=r.json['id'];assert action(t1,{'action':'assignBankExam','id':root,'courseId':cs['10B']}).status_code==200
 delivered=next(r for r in state(pupil)['records'] if r['kind']=='assignment');file=delivered['data']['file']
 assert pupil.get(file['url']).status_code==200
 assert t1.get('/api/library/'+root+'/file').status_code==200
 assert action(t1,{'action':'archiveBankExam','id':root}).status_code==403
 assert action(t2,{'action':'archiveBankExam','id':root}).status_code==200
 assert root not in [r['id'] for r in state(t1)['library']]
 assert pupil.get(file['url']).status_code==200
 # A legacy mismatched assignment is hidden from the pupil and cannot be submitted or downloaded.
 from server import records
 from sqlalchemy import update as sql_update
 with app.extensions['school_engine'].begin() as db:
  data=delivered['data'];data['grade']='11';db.execute(sql_update(records).where(records.c.id==delivered['id']).values(data=json.dumps(data)))
 assert delivered['id'] not in [r['id'] for r in state(pupil)['records']]
 assert pupil.get(file['url']).status_code==403
 assert action(pupil,{'action':'submit','assignmentId':delivered['id'],'text':'essay'}).status_code==403

def test_source_file_and_solution_updates_flow_to_delivered_copy(client,app):
 t1,t2,pupil,cs,ms=prepare(client,app);root=create_exam(t1,cs['10A']);data=copy.deepcopy(root['data']);data['source']='uploaded'
 pdf=b'%PDF-1.4\nnew exam\n%%EOF'
 result=t1.post('/api/exams/'+root['id']+'/update',data={'data':json.dumps(data),'file':(io.BytesIO(pdf),'exam.pdf')},headers={'Origin':'http://localhost','X-CSRF-Token':token(t1)});assert result.status_code==200,result.json
 assert action(t2,{'action':'assignBankExam','id':root['id'],'courseId':cs['10B']}).status_code==200
 delivered=next(r for r in state(pupil)['records'] if r['kind']=='assignment');assert pupil.get(delivered['data']['file']['url']).data==pdf
 assert pupil.get('/api/exams/'+root['id']+'/file').status_code==403
 def upload(c):return c.post('/api/exams/'+delivered['id']+'/resources',data={'kind':'solution','file':(io.BytesIO(b'Guide'),'guide.txt')},headers={'Origin':'http://localhost','X-CSRF-Token':token(c)})
 assert upload(t2).status_code==403
 assert upload(t1).status_code==200
 copied=next(r for r in state(t2)['records'] if r['id']==delivered['id']);url=copied['data']['resources']['solution']['url'];assert delivered['id'] in url
 assert action(t1,{'action':'assignmentSettings','id':root['id'],'answerGuide':'Hướng dẫn mới'}).status_code==200
 assert next(r for r in state(t2)['records'] if r['id']==delivered['id'])['data']['answerGuide']=='Hướng dẫn mới'
 assert action(t2,{'action':'assignmentSettings','id':delivered['id'],'allowViewAnswers':True}).status_code==200
 assert pupil.get(url).status_code==403
 assert action(pupil,{'action':'submit','assignmentId':delivered['id'],'answers':[1],'text':'Proof'}).status_code==200
 assert pupil.get(url).data==b'Guide'

def test_explicit_class_grade_for_nonstandard_name_and_bank_draft_grade(client,app):
 t1,t2,pupil,cs,ms=prepare(client,app)
 root=create_exam(t1,cs['10A']);cid=cs['11C']
 assert action(client,{'action':'course','id':cid,'name':'Lớp buổi chiều','subject':'Toán','teacherId':ms['teach2'],'grade':'9'}).status_code==200
 assert action(t1,{'action':'assignBankExam','id':root['id'],'courseId':cid}).status_code==400
 assert action(client,{'action':'course','id':cid,'name':'Lớp buổi chiều','subject':'Toán','teacherId':ms['teach2'],'grade':'10'}).status_code==200
 assert action(t1,{'action':'assignBankExam','id':root['id'],'courseId':cid}).status_code==200
 draft=copy.deepcopy(root['data']);draft.update(grade='12',title='Bank grade 12')
 assert action(t1,{'action':'record','kind':'assignment','courseId':cs['10A'],'data':draft}).status_code==200
 assert any(r['data']['title']=='Bank grade 12' for r in state(t2)['library'])
