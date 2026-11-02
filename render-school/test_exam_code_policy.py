import copy
from test_school import app,client,action,state,post,token
from test_school_workflows import school,assignment
from server import assigned_exam

def payload(cid,**extra):
 q={'text':'1+1','answers':['1','2','3','4'],'correct':1}
 return {'action':'record','kind':'assignment','courseId':cid,'data':{'title':'Synthetic exam','body':'Synthetic instructions','type':'quiz','questions':[q],'variants':[{'code':code,'questions':[copy.deepcopy(q)],'essays':[]} for code in ['101','102']],'maxAttempts':0,**extra}}

def test_teacher_can_choose_fixed_at_creation_and_students_cannot_override(school):
 admin,cs,ids,cid,_=school;t=cs['teacher'];p=payload(cid,codePolicy='fixed',fixedExamCode='102');assert action(t,p).status_code==200
 r=next(r for r in state(t)['records'] if r['kind']=='assignment');assert r['data']['codePolicy']=='fixed' and r['data']['fixedExamCode']=='102'
 for student in [cs['stu1'],cs['stu2']]:
  exam=next(a['data'] for a in state(student)['records'] if a['id']==r['id']);assert exam['examCode']=='102';assert 'variants' not in exam;assert 'correct' not in exam['questions'][0]
  assert action(student,{'action':'assignmentSettings','id':r['id'],'codePolicy':'fixed','fixedExamCode':'101'}).status_code==403
 assert action(cs['stu1'],{'action':'submit','assignmentId':r['id'],'examCode':'101','answers':[1]}).status_code==409
 assert action(cs['stu1'],{'action':'submit','assignmentId':r['id'],'examCode':'102','answers':[1]}).status_code==200
 for extra in [dict(codePolicy='bad'),dict(codePolicy='fixed',fixedExamCode='999')]:assert action(t,payload(cid,**extra)).status_code==400

def test_random_assignment_is_stable_and_policy_locks_when_a_pupil_starts(school):
 admin,cs,ids,cid,_=school;t=cs['teacher'];rid=assignment(t,cid,variants=True);student=cs['stu1']
 d=next(r['data'] for r in state(t)['records'] if r['id']==rid)
 for mid in ['synthetic-'+str(i) for i in range(30)]:assert assigned_exam(d,rid,mid)['examCode']==assigned_exam(d,rid,mid)['examCode']
 assert {assigned_exam(d,rid,'synthetic-'+str(i))['examCode'] for i in range(100)}=={'101','102'}
 before=next(r['data']['examCode'] for r in state(student)['records'] if r['id']==rid)
 assert post(student,'/api/exams/'+rid+'/clock',{},token(student)).status_code==200
 assert next(r['data']['codePolicyLocked'] for r in state(t)['records'] if r['id']==rid)
 assert action(t,{'action':'assignmentSettings','id':rid,'codePolicy':'fixed','fixedExamCode':'101'}).status_code==409
 assert next(r['data']['examCode'] for r in state(student)['records'] if r['id']==rid)==before
 assert action(t,{'action':'assignmentSettings','id':rid,'codePolicy':'random'}).status_code==200
 assert action(t,{'action':'assignmentSettings','id':rid,'allowViewScore':True}).status_code==200

def test_bank_assignment_accepts_policy_for_target_class_without_changing_source(school):
 admin,cs,ids,cid,_=school;t=cs['teacher'];assert action(t,payload(cid,bankOnly=True,codePolicy='fixed',fixedExamCode='101')).status_code==200
 root=next(r for r in state(t)['library'] if r['data']['title']=='Synthetic exam')
 assert action(t,{'action':'assignBankExam','id':root['id'],'courseId':cid,'codePolicy':'fixed','fixedExamCode':'102'}).status_code==200
 delivered=next(r for r in state(cs['stu1'])['records'] if r['data'].get('bankSourceId')==root['id']);assert delivered['data']['examCode']=='102'
 assert next(r for r in state(t)['library'] if r['id']==root['id'])['data']['fixedExamCode']=='101'
 assert action(t,{'action':'assignBankExam','id':root['id'],'courseId':cid,'codePolicy':'fixed','fixedExamCode':'999'}).status_code==400
