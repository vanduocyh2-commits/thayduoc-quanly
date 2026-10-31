import json
from datetime import datetime,timezone
from sqlalchemy import select,update
from test_school import app,client,action,state
from test_school_workflows import school,assignment
from server import records
from assignment_reminders import normalize_reminder

R=dict(enabled=True,beforeStart=True,beforeEnd=True,hours=2,students=True,parents=True)
def test_validate_reminder_configuration():
 assert not normalize_reminder(None)['enabled']
 for value in [{**R,'hours':0},{**R,'hours':True},{**R,'students':False,'parents':False},R]:
  try:normalize_reminder(value);assert False
  except ValueError:pass
 assert normalize_reminder(R,'2026-10-31T08:00:00Z','2026-10-31T10:00:00Z')['hours']==2

def test_scheduled_student_messages_and_parent_drafts_are_private_and_idempotent(school,app):
 admin,cs,ids,cid,_=school;t=cs['teacher'];rid=assignment(t,cid);engine=app.extensions['school_engine']
 with engine.begin() as db:
  d=json.loads(db.execute(select(records.c.data).where(records.c.id==rid)).scalar_one());d.update(opensAt='2099-10-31T08:00:00Z',due='2099-10-31T10:00:00Z');db.execute(update(records).where(records.c.id==rid).values(data=json.dumps(d)))
 settings=dict(action='assignmentSettings',id=rid,reminder=R)
 assert action(cs['stu1'],settings).status_code==403
 assert action(cs['other'],settings).status_code==403
 assert action(t,settings).status_code==200
 def run(stamp):
  with engine.begin() as db:return app.extensions['assignment_reminders'](db,datetime.fromisoformat(stamp).replace(tzinfo=timezone.utc).timestamp())
 assert run('2099-10-31T05:59:00')==0
 assert run('2099-10-31T06:00:00')==4
 assert run('2099-10-31T07:00:00')==0
 for user in ['stu1','stu2']:
  view=[r for r in state(cs[user])['records'] if r['kind']=='message'];assert len(view)==1 and view[0]['data']['memberId']==ids[user] and not view[0]['data']['parentReminder']
 teacher_messages=[r for r in state(t)['records'] if r['kind']=='message'];assert len(teacher_messages)==4
 parent=next(r for r in teacher_messages if r['data']['parentReminder']);assert action(t,dict(action='readMessage',id=parent['id'])).status_code==200
 assert action(cs['stu1'],dict(action='readMessage',id=parent['id'])).status_code==403
 assert action(t,dict(action='deleteRecord',id=parent['id'])).status_code==200
 assert run('2099-10-31T07:30:00')==0
 # Submissions suppress deadline reminders, including the parent copy.
 from server import submissions
 from sqlalchemy import insert
 with engine.begin() as db:db.execute(insert(submissions).values(id='synthetic-submission',assignment_id=rid,member_id=ids['stu1'],data=json.dumps(dict(answers=[1],score=10)),created_at='2099-10-31T08:01:00Z'))
 assert run('2099-10-31T08:30:00')==2
 latest=[r for r in state(t)['records'] if r['kind']=='message' and 'hạn nộp' in r['data']['title']];assert len(latest)==2 and all(r['data']['memberId']==ids['stu2'] for r in latest)
 assert run('2099-10-31T10:00:00')==0
 assert action(t,dict(action='closeAssignment',id=rid)).status_code==200
 assert run('2099-10-31T08:45:00')==0
