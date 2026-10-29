import io,json
import pytest
from test_school import app,client,action,setup,state,login,token

@pytest.fixture
def school(client,app):
 setup(client)
 for user,role in [('teacher','teacher'),('other','teacher'),('stu1','student'),('stu2','student')]:
  assert action(client,{'action':'member','username':user,'name':user,'password':'Password123!','role':role}).status_code==200
 ids={m['username']:m['id'] for m in state(client)['members']}
 for name,teacher in [('A','teacher'),('B','other')]:assert action(client,{'action':'course','name':name,'subject':'Toán','teacherId':ids[teacher]}).status_code==200
 courses={c['name']:c['id'] for c in state(client)['courses']};cid=courses['A']
 for user in ['stu1','stu2']:assert action(client,{'action':'enroll','courseId':cid,'memberId':ids[user]}).status_code==200
 clients={user:app.test_client() for user in ['teacher','other','stu1','stu2']}
 for user,c in clients.items():assert login(c,user).status_code==200
 return client,clients,ids,cid,courses['B']

def assignment(t,cid,kind='quiz',variants=False):
 d={'title':'Thi thử','body':'Đề bài','type':kind,'maxAttempts':0,'questions':[]}
 if kind=='quiz':d['questions']=[{'text':'1+1','answers':['1','2','3','4'],'correct':1}]
 if variants:d['variants']=[{'code':code,'questions':d['questions'],'essays':[]} for code in ['101','102']]
 assert action(t,{'action':'record','kind':'assignment','courseId':cid,'data':d}).status_code==200
 return next(r['id'] for r in state(t)['records'] if r['kind']=='assignment')

def submit_file(c,rid,content=b'Bai lam',name='bai-lam.txt',text=''):
 return c.post('/api/submissions',data={'payload':json.dumps({'action':'submit','assignmentId':rid,'text':text}),'files':(io.BytesIO(content),name)},headers={'Origin':'http://localhost','X-CSRF-Token':token(c)})

def test_attendance_batch_sessions_retry_stale_and_permissions(school):
 admin,cs,ids,cid,other_cid=school;t=cs['teacher'];entries=[{'memberId':ids[u],'status':'Có mặt'} for u in ['stu1','stu2']]
 p={'action':'attendanceBatch','courseId':cid,'date':'2026-10-30','session':'Sáng','entries':entries,'expected':[]}
 assert action(cs['stu1'],p).status_code==403
 assert action(cs['other'],p).status_code==403
 assert action(t,{**p,'date':'2026-02-30'}).status_code==400
 assert action(t,{**p,'entries':entries[:1]}).status_code==409
 assert not [r for r in state(t)['records'] if r['kind']=='attendance']
 assert action(t,p).status_code==200
 morning=[r for r in state(t)['records'] if r['kind']=='attendance'];assert len(morning)==2
 assert action(t,p).status_code==409
 assert action(t,{**p,'session':'Chiều'}).status_code==200
 version=sorted([{'id':r['id'],'updatedAt':r['data']['updatedAt']} for r in morning],key=lambda r:r['id'])
 edited=[{**entries[0],'status':'Đi muộn'},entries[1]]
 assert action(t,{**p,'expected':version,'replace':True,'entries':edited}).status_code==200
 assert action(t,{**p,'expected':version,'replace':True}).status_code==409
 allrows=[r for r in state(t)['records'] if r['kind']=='attendance'];assert len(allrows)==4
 assert next(r for r in allrows if r['data']['memberId']==ids['stu1'] and r['data']['session']=='Sáng')['data']['status']=='Đi muộn'
 assert next(r for r in allrows if r['data']['memberId']==ids['stu1'] and r['data']['session']=='Chiều')['data']['status']=='Có mặt'
 assert len([r for r in state(cs['stu1'])['records'] if r['kind']=='attendance'])==2

def test_results_publishing_codes_close_and_roster_restore(school):
 admin,cs,ids,cid,_=school;t=cs['teacher'];s=cs['stu1'];rid=assignment(t,cid,variants=True)
 settings={'action':'assignmentSettings','id':rid,'codePolicy':'fixed','fixedExamCode':'102','allowViewScore':False,'allowViewAnswers':True,'answerGuide':'Hướng dẫn giải'}
 assert action(cs['other'],settings).status_code==403
 assert action(t,settings).status_code==200
 view=next(r for r in state(s)['records'] if r['id']==rid)['data'];assert view['examCode']=='102' and 'correct' not in view['questions'][0] and 'answerGuide' not in view
 for answer in [1,0]:assert action(s,{'action':'submit','assignmentId':rid,'answers':[answer]}).status_code==200
 sub=state(t)['submissions'][0];assert sub['data']['bestScore']==10 and sub['data']['score']==0
 hidden=state(s)['submissions'][0]['data'];assert hidden['scoreHidden'] and hidden['bestScore'] is None
 for row in [hidden]+hidden['history']+hidden['attemptScores']+[hidden['bestAttempt']]:assert row['score'] is None and 'quizScore' not in row
 view=next(r for r in state(s)['records'] if r['id']==rid)['data'];assert view['questions'][0]['correct']==1 and view['answerGuide']=='Hướng dẫn giải'
 assert action(t,{'action':'assignmentSettings','id':rid,'codePolicy':'random'}).status_code==409
 assert action(t,{'action':'assignmentSettings','id':rid,'allowViewScore':True}).status_code==200
 assert state(s)['submissions'][0]['data']['bestScore']==10
 assert action(t,{'action':'closeAssignment','id':rid}).status_code==200
 assert action(s,{'action':'submit','assignmentId':rid,'answers':[1]}).status_code==409
 assert action(t,{'action':'grade','id':sub['id'],'attemptCount':1,'score':8,'feedback':'Sửa chấm'}).status_code==200
 assert state(s)['submissions'][0]['data']['bestScore']==8
 # Approved upload is linked to both enrollment and gradebook and is recoverable.
 assert action(t,{'action':'submitRoster','courseId':cid,'students':[{'code':'stu1','name':'stu1'}]}).status_code==200
 roster=state(t)['rosters'][0];assert action(admin,{'action':'approveRoster','id':roster['id']}).status_code==200
 assert action(cs['other'],{'action':'removeRosterStudent','courseId':cid,'memberId':ids['stu1']}).status_code==403
 assert action(t,{'action':'removeRosterStudent','courseId':cid,'memberId':ids['stu1']}).status_code==200
 assert state(t)['rosters'][0]['data']==[] and not state(t)['submissions']
 assert not state(s)['courses'] and not state(s)['submissions']
 removed=state(t)['removedStudents'][0]
 assert action(t,{'action':'restoreRosterStudent','id':removed['id']}).status_code==200
 assert state(s)['submissions'][0]['data']['bestScore']==8
 assert len(state(t)['rosters'][0]['data'])==1
 assert not state(t)['removedStudents']

def test_essay_file_only_retake_privacy_and_resource_publication(school):
 admin,cs,ids,cid,_=school;t=cs['teacher'];s=cs['stu1'];rid=assignment(t,cid,'essay')
 assert submit_file(s,rid,b'not image','bad.png').status_code==400
 assert submit_file(s,rid).status_code==200
 sub=state(t)['submissions'][0];url=sub['data']['attachments'][0]['url']
 assert t.get(url).data==b'Bai lam' and s.get(url).status_code==200
 assert cs['stu2'].get(url).status_code==403 and cs['other'].get(url).status_code==403
 assert submit_file(s,rid,b'second').status_code==200
 assert t.get(url).data==b'Bai lam'
 sub=state(t)['submissions'][0];assert sub['data']['history'][0]['attachments'][0]['url']==url
 assert action(t,{'action':'grade','id':sub['id'],'attemptCount':1,'score':9}).status_code==200
 assert action(t,{'action':'grade','id':sub['id'],'attemptCount':2,'score':5}).status_code==200
 assert state(s)['submissions'][0]['data']['bestScore']==9
 def upload(c):return c.post('/api/exams/'+rid+'/resources',data={'kind':'solution','file':(io.BytesIO(b'Huong dan'),'giai.txt')},headers={'Origin':'http://localhost','X-CSRF-Token':token(c)})
 assert upload(cs['other']).status_code==403
 assert upload(t).status_code==200
 resource='/api/exams/'+rid+'/resources/solution'
 assert s.get(resource).status_code==403
 assert action(t,{'action':'assignmentSettings','id':rid,'allowViewAnswers':True}).status_code==200
 assert s.get(resource).data==b'Huong dan'
 assert cs['stu2'].get(resource).status_code==403
 assert action(t,{'action':'removeRosterStudent','courseId':cid,'memberId':ids['stu1']}).status_code==200
 assert s.get(url).status_code==403 and t.get(url).status_code==403
 assert action(t,{'action':'deleteRecord','id':rid}).status_code==200
 assert t.get(url).status_code==404

def test_new_roster_students_sync_and_removed_attendance_does_not_block_edit(school):
 admin,cs,ids,cid,_=school;t=cs['teacher']
 assert action(t,{'action':'submitRoster','courseId':cid,'students':[{'code':'newpupil','name':'Học sinh mới'}]}).status_code==200
 roster=state(t)['rosters'][0]
 assert not any(m['name']=='Học sinh mới' for m in state(t)['members'])
 assert action(admin,{'action':'approveRoster','id':roster['id']}).status_code==200
 pupil=next(m for m in state(t)['members'] if m['name']=='Học sinh mới')
 assert any(e['course_id']==cid and e['member_id']==pupil['id'] for e in state(t)['enrollments'])
 assert not state(t)['submissions']
 members=[ids['stu1'],ids['stu2'],pupil['id']]
 p={'action':'attendanceBatch','courseId':cid,'date':'2026-10-30','session':'Sáng','entries':[{'memberId':mid,'status':'Có mặt'} for mid in members]}
 assert action(t,p).status_code==200
 assert action(t,{'action':'removeRosterStudent','courseId':cid,'memberId':pupil['id']}).status_code==200
 existing=[r for r in state(t)['records'] if r['kind']=='attendance']
 version=sorted([{'id':r['id'],'updatedAt':r['data']['updatedAt']} for r in existing],key=lambda r:r['id'])
 assert len(version)==2
 assert action(t,{**p,'entries':p['entries'][:2],'replace':True,'expected':version}).status_code==200

def test_multipart_limits_and_exam_policy_mismatch(school):
 admin,cs,ids,cid,_=school;t=cs['teacher'];s=cs['stu1'];rid=assignment(t,cid,variants=True)
 assert submit_file(s,rid).status_code==400
 assert action(t,{'action':'assignmentSettings','id':rid,'codePolicy':'fixed','fixedExamCode':'101'}).status_code==200
 for user in ['stu1','stu2']:assert next(r for r in state(cs[user])['records'] if r['id']==rid)['data']['examCode']=='101'
 assert action(s,{'action':'submit','assignmentId':rid,'answers':[1],'examCode':'102'}).status_code==409
 essay=assignment(t,cid,'essay')
 headers={'Origin':'http://localhost','X-CSRF-Token':token(s)}
 payload=json.dumps({'action':'submit','assignmentId':essay,'text':'attached'})
 assert s.post('/api/submissions',data={'payload':payload,'files':[(io.BytesIO(b'x'),str(i)+'.txt') for i in range(6)]},headers=headers).status_code==400
 assert submit_file(s,essay,b'x'*(5*1024*1024+1)).status_code==400
 assert not state(t)['submissions']
