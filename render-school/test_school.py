import pytest
from server import create_app,members,sessions
from sqlalchemy import select

@pytest.fixture
def app(tmp_path):return create_app({'TESTING':True,'SECRET_KEY':'x'*40,'DATABASE_URL':'sqlite:///'+str(tmp_path/'school.db'),'ADMIN_SETUP_TOKEN':'setup-'+'z'*32})
@pytest.fixture
def client(app):return app.test_client()
def post(c,path,p,csrf=None,origin='http://localhost'):
 headers={'Origin':origin}
 if csrf:headers['X-CSRF-Token']=csrf
 return c.post(path,json=p,headers=headers)
def token(c):return c.get('/api/auth').json['csrf']
def action(c,p):return post(c,'/api/school',p,token(c))
def login(c,u,p='Password123!'):return post(c,'/api/login',{'username':u,'password':p})
def setup(c):return post(c,'/api/setup',{'setupToken':'setup-'+'z'*32,'name':'Thầy Được','username':'admin','password':'Password123!'})
def state(c):return c.get('/api/school').json

def test_admin_and_auth(client,app):
 assert client.get('/healthz').status_code==200
 assert client.get('/api/school').status_code==401
 assert client.get('/api/auth').json['setupNeeded']
 assert post(client,'/api/setup',{'setupToken':'wrong'}).status_code==403
 assert setup(client).status_code==200
 assert state(client)['me']['role']=='admin'
 assert post(client,'/api/setup',{}).status_code==409
 assert 'password_hash' not in state(client)['me']
 assert post(client,'/api/school',{'action':'course'}).status_code==403
 assert post(client,'/api/school',{'action':'course'},token(client),origin='https://bad.test').status_code==403
 assert action(client,{'action':'member','name':'GV','username':'teacher','password':'short','role':'teacher'}).status_code==400
 assert post(client,'/api/logout',{},token(client)).status_code==200
 assert client.get('/api/school').status_code==401
 assert login(client,'admin','bad').status_code==401
 assert login(client,'admin').status_code==200
 with app.extensions['school_engine'].connect() as db:
  row=db.execute(select(members)).mappings().first()
  assert row['password_hash']!='Password123!'
  session=db.execute(select(sessions)).mappings().first()
  assert session['token_hash']!=client.get_cookie('school_session').value

def test_permissions_and_learning(client,app):
 setup(client)
 for username,role in [('math','teacher'),('lit','teacher'),('hs1','student'),('hs2','student')]:
  assert action(client,{'action':'member','name':username,'username':username,'password':'Password123!','email':'','role':role}).status_code==200
 ms={m['username']:m['id'] for m in state(client)['members']}
 for subject,teacher in [('Toán','math'),('Văn','lit')]:assert action(client,{'action':'course','name':'10A1','subject':subject,'teacherId':ms[teacher]}).status_code==200
 cs={c['subject']:c['id'] for c in state(client)['courses']}
 for subject,student in [('Toán','hs1'),('Văn','hs2')]:assert action(client,{'action':'enroll','courseId':cs[subject],'memberId':ms[student]}).status_code==200
 c_math=app.test_client();c_lit=app.test_client();s1=app.test_client();s2=app.test_client()
 for c,u in [(c_math,'math'),(c_lit,'lit'),(s1,'hs1'),(s2,'hs2')]:assert login(c,u).status_code==200
 assert len(state(c_math)['courses'])==1
 assert len(state(s1)['courses'])==1
 assert not any(m['id']==ms['hs2'] for m in state(s1)['members'])
 assert action(c_math,{'action':'member','name':'bad','username':'bad','password':'Password123!','role':'teacher'}).status_code==403
 quiz={'title':'Quiz','body':'Câu hỏi','type':'quiz','due':'','questions':[{'text':'1+1?','answers':['1','2','3','4'],'correct':1}]}
 assert action(c_math,{'action':'record','courseId':cs['Văn'],'kind':'assignment','data':quiz}).status_code==403
 assert action(c_math,{'action':'record','courseId':cs['Toán'],'kind':'assignment','data':quiz}).status_code==200
 a=state(c_math)['records'][0]['id']
 assert state(c_math)['records'][0]['data']['questions'][0]['correct']==1
 assert 'correct' not in state(s1)['records'][0]['data']['questions'][0]
 assert action(s2,{'action':'submit','assignmentId':a,'answers':[1]}).status_code==403
 assert action(s1,{'action':'submit','assignmentId':a,'answers':[1]}).status_code==200
 assert action(s1,{'action':'submit','assignmentId':a,'answers':[1]}).status_code==409
 sub=state(s1)['submissions'][0];assert sub['data']['score']==10
 assert state(s2)['submissions']==[]
 assert action(c_lit,{'action':'grade','id':sub['id'],'score':9}).status_code==403
 assert action(s1,{'action':'grade','id':sub['id'],'score':9}).status_code==403
 assert action(c_math,{'action':'grade','id':sub['id'],'score':8,'feedback':'Tốt'}).status_code==200
 assert state(s1)['submissions'][0]['data']['score']==8
 for status in ['Có mặt','Học bù']:
  assert action(c_math,{'action':'record','courseId':cs['Toán'],'kind':'attendance','data':{'date':'2026-10-29','status':status,'memberId':ms['hs1']}}).status_code==200
 assert len([r for r in state(s1)['records'] if r['kind']=='attendance'])==1
 assert action(c_math,{'action':'record','courseId':cs['Toán'],'kind':'attendance','data':{'date':'2026-10-29','status':'Có mặt','memberId':ms['hs2']}}).status_code==400
 assert action(c_math,{'action':'record','courseId':cs['Toán'],'kind':'message','data':{'title':'Nhận xét','body':'Cố gắng','memberId':ms['hs1']}}).status_code==200
 msg=next(r for r in state(s1)['records'] if r['kind']=='message')
 assert action(s1,{'action':'readMessage','id':msg['id']}).status_code==200
 assert ms['hs1'] in next(r for r in state(s1)['records'] if r['kind']=='message')['data']['readBy']
 assert action(c_lit,{'action':'deleteRecord','id':a}).status_code==403
 assert action(client,{'action':'toggleMember','id':ms['hs1']}).status_code==200
 assert s1.get('/api/school').status_code==401
 assert login(s1,'hs1').status_code==401
 assert action(client,{'action':'toggleMember','id':ms['hs1']}).status_code==200
 assert login(s1,'hs1').status_code==200
 assert action(client,{'action':'resetPassword','id':ms['hs1'],'password':'Changed123!!'}).status_code==200
 assert s1.get('/api/school').status_code==401
 assert login(s1,'hs1','Changed123!!').status_code==200
 assert action(s1,{'action':'password','oldPassword':'Changed123!!','password':'NewPassword123!'}).status_code==200
 assert s1.get('/api/school').status_code==401
 assert login(s1,'hs1','NewPassword123!').status_code==200
 assert action(client,{'action':'deleteRecord','id':a}).status_code==200
 assert state(s1)['submissions']==[]

def test_rate_limit_and_static(client):
 setup(client)
 for _ in range(10):assert login(client,'notfound','bad').status_code==401
 assert login(client,'notfound','bad').status_code==429
 assert client.get('/').status_code==200
 assert b'ChatGPT' not in client.get('/').data
 assert client.get('/healthz').headers['X-Frame-Options']=='DENY'

def test_shared_library_and_file_permissions(client,app):
 import io
 setup(client)
 for user,role in [('teach1','teacher'),('teach2','teacher'),('stud1','student'),('stud2','student')]:
  assert action(client,{'action':'member','name':user,'username':user,'password':'Password123!','role':role}).status_code==200
 ms={m['username']:m['id'] for m in state(client)['members']}
 for name,teacher in [('10A','teach1'),('10B','teach2')]:assert action(client,{'action':'course','name':name,'subject':'Toán','teacherId':ms[teacher]}).status_code==200
 cs={c['name']:c['id'] for c in state(client)['courses']}
 for name,stu in [('10A','stud1'),('10B','stud2')]:assert action(client,{'action':'enroll','courseId':cs[name],'memberId':ms[stu]}).status_code==200
 t1,t2,s1,s2=[app.test_client() for _ in range(4)]
 for c,u in [(t1,'teach1'),(t2,'teach2'),(s1,'stud1'),(s2,'stud2')]:assert login(c,u).status_code==200
 fields={'courseId':cs['10A'],'title':'Bài giảng hàm số','category':'lesson','grade':'10','body':'Khảo sát hàm số','published':'false'}
 def upload(c,fields,filename=None,content=b'%PDF-1.4\nexample'):
  data=dict(fields)
  if filename:data['file']=(io.BytesIO(content),filename)
  return c.post('/api/library',data=data,headers={'Origin':'http://localhost','X-CSRF-Token':token(c)})
 assert upload(s1,fields).status_code==403
 assert upload(t2,fields).status_code==403
 assert upload(t1,fields,'bad.html').status_code==400
 r=upload(t1,fields,'ham-so.pdf');assert r.status_code==200
 rid=r.json['id'];path='/api/library/'+rid+'/file'
 assert len(state(t2)['library'])==1
 assert state(s1)['library']==[]
 assert s1.get(path).status_code==403
 assert app.test_client().get(path).status_code==401
 fields.update(id=rid,published='true')
 assert upload(t1,fields).status_code==200
 assert len(state(s1)['library'])==1
 assert state(s2)['library']==[]
 assert s2.get(path).status_code==403
 file=s1.get(path);assert file.status_code==200 and file.data.startswith(b'%PDF')
 assert file.headers['Content-Disposition'].startswith('attachment;')
 assert file.headers['Cache-Control']=='no-store'
 assert upload(t2,{**fields,'courseId':cs['10B']}).status_code==403
 assert action(t2,{'action':'deleteRecord','id':rid}).status_code==403
 assert upload(t1,{**fields,'removeFile':'true'}).status_code==200
 assert s1.get(path).status_code==404
 assert upload(t1,fields,'moi.txt',b'Noi dung moi').status_code==200
 assert s1.get(path).data==b'Noi dung moi'
 assert action(client,{'action':'deleteRecord','id':rid}).status_code==200
 assert state(t1)['library']==[]
 assert s1.get(path).status_code==404
