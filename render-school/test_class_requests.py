import io,json
from openpyxl import Workbook
from sqlalchemy import insert,select
from test_school import app,client,action,setup,state,login,token,roster_context
from server import class_requests,members,rosters

def teacher_request():return dict(action='requestClass',name='10A1',subject='Vật lí',grade='10',students=[{'code':'000001','name':'Nguyễn Văn A'}])

def test_class_approval_creates_course_and_roster_once_with_private_pending_data(client,app):
 _,t,other=roster_context(client,app);p=teacher_request()
 assert action(t,p).status_code==200
 req=state(t)['classRequests'][0]
 assert not state(other)['classRequests']
 assert not any(c['name']=='10A1' for c in state(client)['courses'])
 assert not any(m['username']=='000001' for m in state(client)['members'])
 assert action(t,p).status_code==409
 assert action(t,dict(action='approveClass',id=req['id'])).status_code==403
 result=action(client,dict(action='approveClass',id=req['id']));assert result.status_code==200
 cid=result.json['courseId'];course=next(c for c in state(t)['courses'] if c['id']==cid)
 assert course['teacher_id']==state(t)['me']['id'] and course['grade']=='10' and course['subject']=='Vật lí'
 assert state(t)['classRequests'][0]['status']=='approved'
 assert any(m['name']=='Nguyễn Văn A' for m in state(t)['members'])
 assert any(e['course_id']==cid for e in state(t)['enrollments'])
 assert state(t)['rosters'][0]['status']=='approved'
 assert 'password' not in json.dumps(state(t)['classRequests'])
 accounts=t.get('/api/student-accounts').json['students'];pupil=next(s for s in accounts if s['username']=='000001');assert pupil['passwordAvailable']
 # Student sees only the approved enrolled course, never class requests or others' rosters.
 with app.extensions['school_engine'].connect() as db:
  student=db.execute(select(members).where(members.c.id==pupil['id'])).mappings().first()
 assert student
 assert action(client,dict(action='resetPassword',id=pupil['id'],password='abcdef')).status_code==200
 hs=app.test_client();assert login(hs,'000001','abcdef').status_code==200
 assert state(hs)['classRequests']==[] and len(state(hs)['courses'])==1
 assert action(hs,teacher_request()).status_code==403
 assert action(client,dict(action='approveClass',id=req['id'])).status_code==409
 assert action(t,p).status_code==409
 # Uploads to an approved class apply directly and preserve existing credentials/enrollment.
 add=action(t,dict(action='submitRoster',courseId=cid,students=p['students']+[{'code':'000002','name':'Trần Văn B'}]))
 assert add.status_code==200 and add.json['credentials'][0]['password']==''
 assert len([e for e in state(t)['enrollments'] if e['course_id']==cid])==2
 assert action(other,dict(action='submitRoster',courseId=cid,students=p['students'])).status_code==403

def test_rejection_and_collision_are_atomic_and_pending_not_shared(client,app):
 _,t,other=roster_context(client,app)
 p=teacher_request();p['students']=[{'code':'newone','name':'Học sinh mới'},{'code':'math','name':'Không trùng tài khoản giáo viên'}]
 assert action(t,p).status_code==200
 req=state(t)['classRequests'][0]
 assert action(client,dict(action='approveClass',id=req['id'])).status_code==409
 assert state(t)['classRequests'][0]['status']=='pending'
 assert not any(c['name']=='10A1' for c in state(client)['courses'])
 assert not any(m['username']=='newone' for m in state(client)['members'])
 assert action(other,dict(action='rejectClass',id=req['id'])).status_code==403
 assert action(client,dict(action='rejectClass',id=req['id'])).status_code==200
 assert not any(c['name']=='10A1' for c in state(client)['courses'])
 assert action(t,teacher_request()).status_code==200
 assert action(t,{**teacher_request(),'grade':'13','name':'invalid'}).status_code==400
 # Pending teacher registration or disabled teacher cannot bypass normal account authentication.
 assert action(client,dict(action='toggleMember',id=state(t)['me']['id'])).status_code==200
 pending=next(r for r in state(client)['classRequests'] if r['status']=='pending')
 assert action(client,dict(action='approveClass',id=pending['id'])).status_code==409

def test_new_class_excel_preview_without_active_course_and_legacy_pending_roster(client,app):
 cid,t,other=roster_context(client,app)
 w=Workbook();w.active.append(['Mã định danh Bộ GD&ĐT','Họ và tên']);w.active.append(['000003','Học Sinh C']);buf=io.BytesIO();w.save(buf)
 result=t.post('/api/student-roster/preview',data={'newClass':'true','file':(io.BytesIO(buf.getvalue()),'lop.xlsx')},headers={'Origin':'http://localhost','X-CSRF-Token':token(t)})
 assert result.status_code==200 and result.json['students'][0]['code']=='000003'
 # Pre-existing pending roster uploads remain reviewable after upgrade.
 with app.extensions['school_engine'].begin() as db:
  db.execute(insert(rosters).values(id='legacy-pending',course_id=cid,author_id=state(t)['me']['id'],data=json.dumps([{'code':'old001','name':'Học Sinh Cũ'}]),status='pending',created_at='2026-10-31'))
 result=action(client,dict(action='approveRoster',id='legacy-pending'));assert result.status_code==200
 assert any(m['name']=='Học Sinh Cũ' for m in state(t)['members'])

def test_library_uses_course_subject_and_rejects_mismatched_subject(client,app):
 cid,t,other=roster_context(client,app)
 def save(subject):return t.post('/api/library',data={'title':'Tài liệu Toán','body':'Nội dung','category':'lesson','grade':'12','courseId':cid,'subject':subject},headers={'Origin':'http://localhost','X-CSRF-Token':token(t)})
 assert save('Văn').status_code==400
 assert not state(t)['library']
 assert save('Toán').status_code==200
 assert state(t)['library'][0]['data']['subject']=='Toán'
 # Course rename moves existing documents to the correct subject group without losing files/records.
 teacher=state(t)['me']['id']
 assert action(client,dict(action='course',id=cid,name='12A1',subject='Vật lí',teacherId=teacher)).status_code==200
 assert state(t)['library'][0]['data']['subject']=='Vật lí'
 assert action(other,dict(action='deleteRecord',id=state(t)['library'][0]['id'])).status_code==403
