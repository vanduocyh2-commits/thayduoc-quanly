"""Synthetic accounts only; these tests never connect to the deployed school."""
import io,json
from sqlalchemy import delete,select
from openpyxl import load_workbook
from test_school import app,client,token,post,login,action,state
from test_student_accounts import prepare
from server import members,student_credentials,account_audits

def issue(c,ids,replace=False,students=None):
 listed={s['id']:s for s in c.get('/api/student-accounts').json['students']}
 payload={'confirmed':True,'replaceExisting':replace,'students':students or [{'id':mid,'version':listed[mid]['version']} for mid in ids]}
 return post(c,'/api/student-accounts/bulk-passwords',payload,token(c))

def test_missing_only_bulk_preserves_other_students_and_exports_six_character_password(client,app):
 t1,t2,s1,s2,ids,cs=prepare(client,app)
 with app.extensions['school_engine'].begin() as db:db.execute(delete(student_credentials).where(student_credentials.c.member_id==ids['student1']))
 before=state(client)
 result=issue(client,[ids['student1'],ids['student2']]);assert result.status_code==200 and result.headers['Cache-Control']=='no-store'
 assert result.json['updated']==1 and result.json['skipped']==1 and result.json['updatedIds']==[ids['student1']]
 revealed=post(t1,'/api/student-accounts/'+ids['student1']+'/reveal',{},token(t1)).json['password'];assert len(revealed)==6 and revealed not in result.text
 assert s1.get('/api/school').status_code==401 and s2.get('/api/school').status_code==200
 assert login(s1,'student1',revealed).status_code==200
 after=state(client)
 for field in ['courses','enrollments','records','submissions','rosters']:assert before[field]==after[field]
 exported=post(t1,'/api/student-accounts/export',{'ids':[ids['student1']],'includePasswords':True},token(t1));sheet=load_workbook(io.BytesIO(exported.data)).active;assert sheet['D2'].value==revealed
 with app.extensions['school_engine'].connect() as db:
  audits=[dict(a) for a in db.execute(select(account_audits)).mappings()];assert any(a['action']=='password_bulk_issue' for a in audits);assert revealed not in json.dumps(audits)
  assert revealed not in db.execute(select(student_credentials.c.encrypted_password).where(student_credentials.c.member_id==ids['student1'])).scalar_one()

def test_bulk_all_issues_distinct_passwords_and_teacher_is_limited_to_own_students(client,app):
 t1,t2,s1,s2,ids,cs=prepare(client,app)
 result=issue(client,[ids['student1'],ids['student2']],True);assert result.status_code==200 and result.json['updated']==2
 passwords=[post(client,'/api/student-accounts/'+ids[u]+'/reveal',{},token(client)).json['password'] for u in ['student1','student2']]
 assert len(set(passwords))==2 and all(len(p)==6 for p in passwords)
 assert issue(t1,[ids['student1']],True).status_code==200
 outside=[{'id':ids['student1'],'version':t1.get('/api/student-accounts').json['students'][0]['version']},{'id':ids['student2'],'version':'0'*64}]
 assert issue(t1,[],True,outside).status_code==403
 assert login(s2,'student2',passwords[1]).status_code==200

def test_bulk_validates_confirmation_csrf_selection_and_roles(client,app):
 t1,t2,s1,s2,ids,cs=prepare(client,app);student=t1.get('/api/student-accounts').json['students'][0];row={'id':student['id'],'version':student['version']};p={'confirmed':True,'students':[row]}
 assert post(t1,'/api/student-accounts/bulk-passwords',p).status_code==403
 for bad in [{**p,'confirmed':False},{**p,'students':[]},{**p,'students':[row,row]},{**p,'students':[row]*501},{**p,'students':[{'id':row['id']}]},{**p,'replaceExisting':'yes'}]:assert post(t1,'/api/student-accounts/bulk-passwords',bad,token(t1)).status_code==400
 assert post(s1,'/api/student-accounts/bulk-passwords',p,token(s1)).status_code==403
 assert post(app.test_client(),'/api/student-accounts/bulk-passwords',p).status_code==401
 assert login(s1,'student1').status_code==200

def test_stale_review_and_failure_are_atomic(client,app,monkeypatch):
 t1,t2,s1,s2,ids,cs=prepare(client,app)
 with app.extensions['school_engine'].begin() as db:db.execute(delete(student_credentials).where(student_credentials.c.member_id==ids['student1']))
 listed=client.get('/api/student-accounts').json['students'];review=[{'id':s['id'],'version':s['version']} for s in listed]
 assert action(s1,{'action':'password','oldPassword':'Password123!','password':'Changed123!'}).status_code==200
 assert issue(client,[],True,review).status_code==409
 assert login(s2,'student2').status_code==200
 import server
 original=server.seal_password;calls=0
 def fail_second(*args):
  nonlocal calls
  calls+=1
  if calls==2:raise RuntimeError('Synthetic transaction failure')
  return original(*args)
 monkeypatch.setattr(server,'seal_password',fail_second);app.config['PROPAGATE_EXCEPTIONS']=False
 assert issue(client,[ids['student1'],ids['student2']],True).status_code==500
 assert login(s1,'student1','Changed123!').status_code==200
 assert login(s2,'student2').status_code==200
 with app.extensions['school_engine'].connect() as db:assert not db.execute(select(account_audits).where(account_audits.c.action=='password_bulk_issue')).first()
