from sqlalchemy import select
from werkzeug.security import check_password_hash
from test_school import app,client,setup,login,token,post,action,state
from test_school_workflows import school
from server import teacher_registrations,members

P=dict(name='Synthetic teacher',username='new.teacher',email='teacher@example.test',password='Synthetic123!')
def register(c,**extra):return post(c,'/api/teacher-registration',{**P,**extra})

def test_signup_pending_until_admin_approval_and_no_automatic_class_access(school,app):
 admin,cs,ids,cid,_=school;anon=app.test_client();r=register(anon,role='admin',disabled=0);assert r.status_code==200 and not r.headers.get('Set-Cookie') and 'Synthetic123!' not in r.text
 assert login(anon,P['username'],P['password']).status_code==401
 pending=state(admin)['teacherRegistrations'];assert len(pending)==1 and 'password_hash' not in pending[0];rid=pending[0]['id']
 for user in ['teacher','stu1']:
  assert state(cs[user])['teacherRegistrations']==[]
  assert action(cs[user],dict(action='approveTeacherRegistration',id=rid)).status_code==403
 assert post(anon,'/api/school',dict(action='approveTeacherRegistration',id=rid)).status_code==401
 assert action(admin,dict(action='approveTeacherRegistration',id=rid)).status_code==200
 assert action(admin,dict(action='approveTeacherRegistration',id=rid)).status_code==409
 assert login(anon,P['username'],P['password']).status_code==200
 view=state(anon);assert view['me']['role']=='teacher' and not view['courses'] and not view['enrollments'] and not view['records'] and not view['submissions']
 assert not anon.get('/api/student-accounts').json['students']
 with app.extensions['school_engine'].connect() as db:
  member=db.execute(select(members).where(members.c.username==P['username'])).mappings().one();assert check_password_hash(member['password_hash'],P['password'])
  assert db.execute(select(teacher_registrations.c.password_hash).where(teacher_registrations.c.id==rid)).scalar_one()==''

def test_rejection_reapply_validation_and_username_collision(client,app):
 assert register(client).status_code==409
 setup(client);anon=app.test_client()
 assert post(anon,'/api/teacher-registration',P,origin='https://unrelated.test').status_code==403
 for bad in [dict(username='bad spaces'),dict(name=''),dict(password='short'),dict(email='bad-email')]:assert register(anon,**bad).status_code==400
 assert register(anon).status_code==200
 assert register(anon).status_code==409
 rid=state(client)['teacherRegistrations'][0]['id'];assert action(client,dict(action='rejectTeacherRegistration',id=rid)).status_code==200
 assert login(anon,P['username'],P['password']).status_code==401
 assert register(anon,password='Replacement123!').status_code==200
 assert action(client,dict(action='member',username=P['username'],name='Different account',password='Unchanged123!',role='teacher')).status_code==200
 assert action(client,dict(action='approveTeacherRegistration',id=rid)).status_code==409
 assert login(anon,P['username'],'Unchanged123!').status_code==200

def test_registration_rate_limited(client,app):
 setup(client);anon=app.test_client()
 for i in range(30):assert register(anon,username='rateuser'+str(i)).status_code==200
 assert register(anon,username='rateuser31').status_code==429
