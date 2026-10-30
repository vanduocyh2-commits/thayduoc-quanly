import json,time
from datetime import datetime,timezone
from sqlalchemy import select,update
from test_school import app,client,action,state,post,token
from test_student_accounts import prepare
from server import exam_clocks,records

def exam(t,cid,**extra):
 data={'title':'Đồng hồ thử nghiệm','body':'Đề thử','type':'quiz','minutes':90,'maxAttempts':0,'questions':[{'text':'1+1','answers':['1','2','3','4'],'correct':1}],**extra}
 assert action(t,{'action':'record','kind':'assignment','courseId':cid,'data':data}).status_code==200
 return next(r for r in state(t)['records'] if r['kind']=='assignment')

def clock(c,r):return post(c,'/api/exams/'+r['id']+'/clock',{},token(c))

def test_clock_uses_server_start_and_is_idempotent_across_reopening(client,app,monkeypatch):
 t1,t2,s1,s2,ids,cs=prepare(client,app);r=exam(t1,cs['10A']);initial=clock(s1,r)
 assert initial.status_code==200
 d=initial.json;assert d['deadline']-d['startedAt']==90*60000 and d['attempt']==1
 current=time.time();monkeypatch.setattr('server.time.time',lambda:current+15)
 again=clock(s1,r).json
 assert again['startedAt']==d['startedAt'] and again['deadline']==d['deadline'] and again['serverNow']>d['serverNow']
 with app.extensions['school_engine'].connect() as db:assert len(db.execute(select(exam_clocks)).all())==1
 assert action(s1,{'action':'submit','assignmentId':r['id'],'answers':[1]}).status_code==200
 following=clock(s1,r).json
 assert following['attempt']==2 and following['startedAt']>d['startedAt']

def test_clock_caps_at_due_and_enforces_access_csrf_and_availability(client,app):
 t1,t2,s1,s2,ids,cs=prepare(client,app)
 due=datetime.fromtimestamp(time.time()+600,timezone.utc).isoformat();r=exam(t1,cs['10A'],due=due)
 d=clock(s1,r).json;assert d['deadline']<=int(datetime.fromisoformat(due).timestamp())*1000 and d['deadline']-d['startedAt']<=600000
 assert clock(s2,r).status_code==403
 assert clock(t1,r).status_code==403
 assert post(s1,'/api/exams/'+r['id']+'/clock',{}).status_code==403
 with app.extensions['school_engine'].begin() as db:
  data=json.loads(db.execute(select(records.c.data).where(records.c.id==r['id'])).scalar_one());data['closedAt']=datetime.now(timezone.utc).isoformat();db.execute(update(records).where(records.c.id==r['id']).values(data=json.dumps(data)))
 assert clock(s1,r).status_code==409

def test_untimed_clock_and_expired_timer_do_not_reset(client,app,monkeypatch):
 t1,t2,s1,s2,ids,cs=prepare(client,app);r=exam(t1,cs['10A'],minutes=1,maxAttempts=1)
 d=clock(s1,r).json;current=time.time();monkeypatch.setattr('server.time.time',lambda:current+120)
 assert clock(s1,r).json['deadline']==d['deadline']
 assert action(s1,{'action':'submit','assignmentId':r['id'],'answers':[1]}).status_code==200
 assert clock(s1,r).status_code==409
