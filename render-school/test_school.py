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

def roster_context(client,app):
 setup(client)
 for u in ['math','other']:
  assert action(client,{'action':'member','username':u,'name':u,'role':'teacher','password':'Password123!'}).status_code==200
 ms={m['username']:m['id'] for m in state(client)['members']}
 action(client,{'action':'course','name':'12A1','subject':'Toán','teacherId':ms['math']})
 cid=state(client)['courses'][0]['id'];t=app.test_client();login(t,'math');o=app.test_client();login(o,'other')
 return cid,t,o

def test_roster_approval(client,app):
 cid,t,o=roster_context(client,app)
 students=[{'code':'0001234567','name':'Học Sinh A'},{'code':'hs002','name':'Học Sinh B'}]
 p={'action':'submitRoster','courseId':cid,'students':students}
 assert action(o,p).status_code==403
 assert action(t,p).status_code==200
 assert len(state(client)['members'])==3
 rid=state(client)['rosters'][0]['id']
 assert not state(o)['rosters']
 assert action(t,{'action':'approveRoster','id':rid}).status_code==403
 approved=action(client,{'action':'approveRoster','id':rid});assert approved.status_code==200
 creds=approved.json['credentials'];assert len(creds)==2 and all(len(x['password'])>=10 for x in creds)
 assert len(state(t)['enrollments'])==2
 assert action(client,{'action':'approveRoster','id':rid}).status_code==409
 hs=app.test_client();assert login(hs,creds[0]['username'],creds[0]['password']).status_code==200
 assert len(state(hs)['courses'])==1 and state(hs)['rosters']==[]
 assert action(hs,p).status_code==403
 assert 'credentials' not in state(client) and 'password' not in str(state(t)['rosters'])
 # Repeat import preserves existing accounts, passwords and enrolments.
 assert action(t,p).status_code==200
 rid=next(r['id'] for r in state(client)['rosters'] if r['status']=='pending')
 r=action(client,{'action':'approveRoster','id':rid});assert r.status_code==200
 assert all(x['password']=='' for x in r.json['credentials'])
 assert len(state(t)['enrollments'])==2
 assert login(hs,creds[0]['username'],creds[0]['password']).status_code==200
 # A collision aborts the whole transaction, including earlier rows.
 assert action(t,{**p,'students':[{'code':'new123','name':'New'},{'code':'math','name':'Conflict'}]}).status_code==200
 rid=next(r['id'] for r in state(client)['rosters'] if r['status']=='pending')
 assert action(client,{'action':'approveRoster','id':rid}).status_code==409
 assert not any(m['username']=='new123' for m in state(client)['members'])
 assert action(client,{'action':'rejectRoster','id':rid}).status_code==200
 assert action(t,{**p,'students':[students[0],students[0]]}).status_code==400

def test_roster_excel(client,app):
 import io
 from openpyxl import Workbook
 cid,t,o=roster_context(client,app)
 def upload(c,raw):return c.post('/api/student-roster/preview',data={'courseId':cid,'file':(io.BytesIO(raw),'csdl.xlsx')},headers={'Origin':'http://localhost','X-CSRF-Token':token(c)})
 w=Workbook();s=w.active;s.append(['TRƯỜNG THPT']);s.append(['BẢNG ĐIỂM HỌC KỲ']);s.append(['STT','Mã định danh Bộ GD&ĐT','Họ và tên','Ngày sinh']);s.append([None,None,None,1]);s.append([1,'0012345678','Nguyễn Văn A','01/01/2009']);s.append([2,1786966155,'Trần Văn B']);s.append(['Tổng cộng']);out=io.BytesIO();w.save(out)
 r=upload(t,out.getvalue());assert r.status_code==200
 assert [x['code'] for x in r.json['students']]==['0012345678','1786966155'] and not r.json['errors']
 assert upload(o,out.getvalue()).status_code==403
 assert upload(t,b'not excel').status_code==400
 s.append([3,'0012345678','Trùng']);out=io.BytesIO();w.save(out)
 assert upload(t,out.getvalue()).json['errors']
 template=t.get('/api/student-roster/template');assert template.status_code==200
 assert client.get('/api/student-roster/template').status_code==200

def test_pdf_and_mixed_exam(client,app):
 import io,json
 setup(client)
 for u,role in [('teacher','teacher'),('student','student'),('outsider','student')]:
  assert action(client,dict(action='member',name=u,username=u,password='Password123!',role=role)).status_code==200
 ms={m['username']:m['id'] for m in state(client)['members']}
 action(client,dict(action='course',name='12A1',subject='Toán',teacherId=ms['teacher']))
 cid=state(client)['courses'][0]['id'];action(client,dict(action='enroll',courseId=cid,memberId=ms['student']))
 teacher=app.test_client();student=app.test_client();other=app.test_client()
 login(teacher,'teacher');login(student,'student');login(other,'outsider')
 def upload(d,raw=None):
  data={'payload':json.dumps(dict(action='record',kind='assignment',courseId=cid,data=d))}
  if raw:data['file']=(io.BytesIO(raw),'exam.pdf')
  return teacher.post('/api/exams',data=data,headers={'Origin':'http://localhost','X-CSRF-Token':token(teacher)})
 d=dict(title='Đề PDF',body='Làm bài',type='essay',questions=[],essays=[])
 assert upload(d,b'not pdf').status_code==400
 assert upload(d,b'%PDF-1.4\n'+b'x'*180000).status_code==200
 a=state(teacher)['records'][0];url=a['data']['file']['url']
 assert student.get(url).status_code==200
 assert other.get(url).status_code==403
 assert app.test_client().get(url).status_code==401
 q=dict(text='1+1?',answers=['1','2','3','4'],correct=1,points=4,topic='Số',level='Nhận biết')
 essay=dict(text='Giải thích',points=6,topic='Số',level='Thông hiểu')
 d=dict(title='Đề kết hợp',body='Làm bài',type='mixed',composed=True,questions=[q],essays=[essay])
 assert upload(d).status_code==200
 a=next(r for r in state(student)['records'] if r['data']['title']=='Đề kết hợp')
 assert 'correct' not in a['data']['questions'][0]
 assert action(student,dict(action='submit',assignmentId=a['id'],answers=[1],text='Giải thích kết quả')).status_code==200
 sub=state(teacher)['submissions'][0]
 assert sub['data']['quizScore']==4 and sub['data']['score'] is None
 assert action(teacher,dict(action='grade',id=sub['id'],score=9,feedback='Tốt')).status_code==200
 d['essays'][0]['points']=5
 assert upload(d).status_code==400
 a=next(r for r in state(teacher)['records'] if r['data']['title']=='Đề PDF')
 assert action(teacher,dict(action='deleteRecord',id=a['id'])).status_code==200
 assert student.get(url).status_code==404

def test_four_types_variants_and_answer_privacy(client,app):
 import json,copy
 setup(client)
 for u,role in [('teacher','teacher'),('student','student')]:action(client,dict(action='member',name=u,username=u,password='Password123!',role=role))
 ms={m['username']:m['id'] for m in state(client)['members']};action(client,dict(action='course',name='12A',subject='Vật lí',teacherId=ms['teacher']));cid=state(client)['courses'][0]['id'];action(client,dict(action='enroll',courseId=cid,memberId=ms['student']))
 teacher=app.test_client();student=app.test_client();login(teacher,'teacher');login(student,'student')
 common=dict(topic='Chuyển động',level='Thông hiểu',outcome='Vận dụng công thức')
 qs=[dict(common,type='quiz',text='Câu 1',points=2,answers=['A','B','C','D'],correct=1),dict(common,type='truefalse',text='Câu 2',points=2,answers=['a','b','c','d'],correct=[True,False,True,False]),dict(common,type='short',text='Câu 3',points=2,correct='2.5')]
 es=[dict(common,type='essay',text='Câu 4',points=4)]
 variant=dict(code='101',questions=copy.deepcopy(qs[::-1]),essays=copy.deepcopy(es));vq=variant['questions'][2];vq.update(answers=['D','C','B','A'],correct=2)
 d=dict(title='4 dạng',body='Làm bài',type='mixed',composed=True,questions=qs,essays=es,minutes=45,grade='12',tfScoring='progressive',variants=[variant])
 def save(d):return teacher.post('/api/exams',data={'payload':json.dumps(dict(action='record',kind='assignment',courseId=cid,data=d))},headers={'Origin':'http://localhost','X-CSRF-Token':token(teacher)})
 assert save(d).status_code==200
 a=state(student)['records'][0];assert a['data']['examCode']=='101';assert 'variants' not in a['data'];assert 'correct' not in a['data']['questions'][0];assert 'outcome' not in a['data']['essays'][0]
 assert state(student)['records'][0]['data']['questions']==a['data']['questions']
 assert action(student,dict(action='submit',assignmentId=a['id'],answers=['2,5',[True,False,False,False],2],text='Bài giải')).status_code==200
 sub=state(teacher)['submissions'][0];assert sub['data']['examCode']=='101';assert sub['data']['quizScore']==5;assert sub['data']['score'] is None
 bad=copy.deepcopy(d);bad['variants'][0]['questions'][2]['correct']=0;assert save(bad).status_code==400
 bad=copy.deepcopy(d);bad['questions'][1]['correct']=[True];assert save(bad).status_code==400
 bad=copy.deepcopy(d);bad['minutes']=0;assert save(bad).status_code==400
 bad=copy.deepcopy(d);bad['questions'][0]['points']=float('nan');assert save(bad).status_code==400

def test_truefalse_scoring_and_short_normalization():
 from server import auto_question_score,AppError
 q=dict(type='truefalse',points=2,correct=[True,True,True,True])
 for n,fraction in enumerate([0,.1,.25,.5,1]):
  answer=[True]*n+[False]*(4-n)
  assert auto_question_score(q,answer,'progressive',True)==2*fraction
  assert auto_question_score(q,answer,'equal',True)==n*.5
 with pytest.raises(AppError):auto_question_score(q,[True],'equal',True)
 assert auto_question_score(dict(type='short',correct='  2.5 ',points=1),'2,5','equal',True)==1
 assert auto_question_score(dict(type='short',correct='NaCl',points=1),'NACL','equal',True)==0
 assert auto_question_score(dict(type='short',correct='NaCl',points=1,ignoreCase=True),'NACL','equal',True)==1

def test_exam_exports_real_word_math_excel_and_permissions(client,app):
 import io,zipfile
 from openpyxl import load_workbook
 setup(client)
 action(client,dict(action='member',name='GV',username='teacher',password='Password123!',role='teacher'))
 teacher_id=next(m['id'] for m in state(client)['members'] if m['role']=='teacher');action(client,dict(action='course',name='10A',subject='Toán',teacherId=teacher_id));cid=state(client)['courses'][0]['id']
 q=dict(type='short',text=r'Tính $\frac{1}{2}$',correct='0,5',points=10,topic='=1+1',level='Nhận biết',outcome='Tính phân số')
 d=dict(title='Đề phân số',body='Làm bài',composed=True,type='quiz',questions=[q],essays=[],includeMatrix=True,minutes=45,grade='10')
 r=post(client,'/api/exams/export',dict(courseId=cid,data=d),token(client));assert r.status_code==200
 with zipfile.ZipFile(io.BytesIO(r.data)) as z:
  assert set(['de-GOC.docx','dap-an.xlsx','ma-tran-dac-ta-GOC.docx','de-cuong.docx','qr-ma-de-GOC.svg'])<=set(z.namelist())
  with zipfile.ZipFile(io.BytesIO(z.read('de-GOC.docx'))) as word:
   xml=word.read('word/document.xml');assert b'<m:oMath' in xml and b'<m:f>' in xml
   assert b'0,5' not in xml # No answer leaked into the student-facing Word.
  wb=load_workbook(io.BytesIO(z.read('dap-an.xlsx')));ws=wb.active;assert ws['D2'].value=='=1+1';assert ws['D2'].data_type=='s';assert ws['G2'].value=='0,5'
 r=post(client,'/api/exams/export',dict(courseId=cid,data=d,format='outline'),token(client));assert r.status_code==200
 action(client,dict(action='member',name='HS',username='student',password='Password123!',role='student'))
 student=app.test_client();login(student,'student')
 assert post(student,'/api/exams/export',dict(courseId=cid,data=d),token(student)).status_code==403

def upload_test_accounts(client,app):
 setup(client)
 for u,role in [('teacher','teacher'),('other','teacher'),('student','student')]:action(client,dict(action='member',name=u,username=u,password='Password123!',role=role))
 ms={m['username']:m['id'] for m in state(client)['members']};action(client,dict(action='course',name='12A',subject='Ngữ văn',teacherId=ms['teacher']));cid=state(client)['courses'][0]['id'];action(client,dict(action='enroll',courseId=cid,memberId=ms['student']))
 clients={u:app.test_client() for u in ['teacher','other','student']}
 for u,c in clients.items():login(c,u)
 return cid,clients

def test_independent_outlines_drafts_export_and_permissions(client,app):
 import io,zipfile
 cid,cs=upload_test_accounts(client,app);teacher=cs['teacher'];student=cs['student']
 d=dict(title='Ôn tập giữa kỳ',grade='12',published=False,body='Tự ôn tập',sections=[dict(topic='Chủ đề 1',objectives='Hiểu kiến thức',theory=r'Công thức $x^2$',exercises='Bài 1')])
 r=post(teacher,'/api/outlines',dict(courseId=cid,data=d),token(teacher));assert r.status_code==200;rid=r.json['id']
 assert not any(r['kind']=='outline' for r in state(student)['records'])
 assert student.get('/api/outlines/'+rid+'/word').status_code==403
 assert post(cs['other'],'/api/outlines',dict(id=rid,courseId=cid,data=d),token(cs['other'])).status_code==403
 d['published']=True
 assert post(teacher,'/api/outlines',dict(id=rid,courseId=cid,data=d),token(teacher)).status_code==200
 a=next(r for r in state(student)['records'] if r['id']==rid);assert a['data']['subject']=='Ngữ văn'
 word=student.get('/api/outlines/'+rid+'/word');assert word.status_code==200
 with zipfile.ZipFile(io.BytesIO(word.data)) as z:assert b'<m:oMath' in z.read('word/document.xml')
 assert post(student,'/api/outlines',dict(courseId=cid,data=d),token(student)).status_code==403
 assert post(teacher,'/api/outlines/export',dict(courseId=cid,data=d),token(teacher)).status_code==200
 assert post(teacher,'/api/outlines',dict(courseId=cid,data=[]),token(teacher)).status_code==400
 assert action(teacher,dict(action='deleteRecord',id=rid)).status_code==200
 assert student.get('/api/outlines/'+rid+'/word').status_code==404

def test_external_word_text_and_multiple_codes(client,app):
 import io,json,copy
 from docx import Document
 from server import exam_files
 cid,cs=upload_test_accounts(client,app);teacher=cs['teacher'];student=cs['student']
 def inspect(raw,name):return teacher.post('/api/exams/inspect',data={'courseId':cid,'file':(io.BytesIO(raw),name)},headers={'Origin':'http://localhost','X-CSRF-Token':token(teacher)})
 assert inspect(b'not word','x.docx').status_code==400
 assert inspect(b'hello','x.exe').status_code==400
 assert inspect(b'\xff','x.txt').status_code==400
 doc=Document();doc.add_paragraph('Đề Ngữ văn');out=io.BytesIO();doc.save(out);word=out.getvalue()
 r=inspect(word,'de_102.docx');assert r.status_code==200 and 'Đề Ngữ văn' in r.json['preview']
 q=dict(type='quiz',text='Câu 1 theo tệp',points=10,topic='Nội dung',level='Nhận biết',outcome='Làm bài',answers=['A','B','C','D'],correct=0)
 q2={**q,'correct':1};d=dict(title='Nhiều mã đề',body='Làm bài',type='quiz',composed=True,source='uploaded',questions=[q],essays=[],variants=[dict(code='101',questions=[q],essays=[]),dict(code='102',questions=[q2],essays=[])],maxAttempts=2)
 files={'payload':json.dumps(dict(action='record',kind='assignment',courseId=cid,data=d)),'file_101':(io.BytesIO(b'%PDF-1.4\nexample'),'de101.pdf'),'file_102':(io.BytesIO(word),'de102.docx')}
 r=teacher.post('/api/exams',data=files,headers={'Origin':'http://localhost','X-CSRF-Token':token(teacher)});assert r.status_code==200
 a=state(student)['records'][0];code=a['data']['examCode'];url=a['data']['file']['url'];assert code in ['101','102'];assert 'variants' not in a['data'];assert 'correct' not in a['data']['questions'][0]
 other='102' if code=='101' else '101';assert student.get('/api/exams/'+a['id']+'/files/'+other).status_code==403
 assert teacher.get('/api/exams/'+a['id']+'/files/'+other).status_code==200
 r=student.get(url);assert r.status_code==200
 pdf=teacher.get('/api/exams/'+a['id']+'/files/101?preview=1');assert pdf.status_code==200 and pdf.headers['X-Frame-Options']=='SAMEORIGIN' and 'inline' in pdf.headers['Content-Disposition']
 for i in range(2):assert action(student,dict(action='submit',assignmentId=a['id'],answers=[0 if code=='101' else 1])).status_code==200
 sub=state(teacher)['submissions'][0];assert sub['data']['attemptCount']==2 and sub['data']['score']==10 and len(sub['data']['history'])==1
 assert action(student,dict(action='submit',assignmentId=a['id'],answers=[0])).status_code==409
 assert action(teacher,dict(action='deleteRecord',id=a['id'])).status_code==200
 with app.extensions['school_engine'].connect() as db:assert not db.execute(select(exam_files)).first()

def test_opening_time_and_answer_excel(client,app):
 import io,json
 from openpyxl import Workbook
 cid,cs=upload_test_accounts(client,app);teacher=cs['teacher'];student=cs['student']
 q=dict(text='1+1',answers=['1','2','3','4'],correct=1)
 d=dict(title='Hẹn giờ',body='Làm bài',type='quiz',questions=[q],essays=[],opensAt='2100-01-01T00:00:00Z',maxAttempts=0)
 assert action(teacher,dict(action='record',kind='assignment',courseId=cid,data=d)).status_code==200
 a=state(student)['records'][0];assert a['data']['questions']==[]
 assert action(student,dict(action='submit',assignmentId=a['id'],answers=[1])).status_code==400
 wb=Workbook();ws=wb.active;ws.append(['Ma de','Dang','Cau','Dap an']);ws.append(['101','quiz',1,'A']);out=io.BytesIO();wb.save(out)
 r=teacher.post('/api/exams/keys',data={'courseId':cid,'file':(io.BytesIO(out.getvalue()),'keys.xlsx')},headers={'Origin':'http://localhost','X-CSRF-Token':token(teacher)})
 assert r.status_code==200 and r.json['rows'][0]['answer']=='A'
 assert teacher.get('/api/exams/key-template').status_code==200
 assert student.get('/api/exams/key-template').status_code==403

def test_matrix_outline_shared_identity_hierarchy_and_private_instructions(client,app):
 import io,zipfile
 cid,cs=upload_test_accounts(client,app);teacher=cs['teacher'];student=cs['student']
 d=dict(title='Đề cương từ ma trận',grade='12',requirements='Yêu cầu riêng giáo viên',sourceMatrix=[dict(type='quiz',topic='Hàm số',points=.25,counts=[2,1,1,0])],inLibrary=True,published=False,sections=[dict(heading='Ôn tập',chapter='Chương I',lesson='Bài 1',topic='Hàm số',theory='Nội dung trọng tâm')])
 r=post(teacher,'/api/outlines',dict(courseId=cid,data=d),token(teacher));assert r.status_code==200;rid=r.json['id']
 s=state(teacher);a=next(r for r in s['records'] if r['id']==rid);b=next(r for r in s['library'] if r['id']==rid)
 assert a['id']==b['id'] and b['data']['category']=='outline'
 assert b['data']['sections'][0]['chapter']=='Chương I';assert a['data']['sourceMatrix'][0]['counts']==[2,1,1,0]
 assert not any(r['id']==rid for r in state(student)['library'])
 d['title']='Đã chỉnh sửa';d['published']=True
 assert post(teacher,'/api/outlines',dict(id=rid,courseId=cid,data=d),token(teacher)).status_code==200
 s=state(student);a=next(r for r in s['records'] if r['id']==rid);b=next(r for r in s['library'] if r['id']==rid)
 assert a['data']['title']==b['data']['title']=='Đã chỉnh sửa'
 assert 'requirements' not in a['data'] and 'requirements' not in b['data']
 with zipfile.ZipFile(io.BytesIO(student.get('/api/outlines/'+rid+'/word').data)) as z:assert 'Chương I' in z.read('word/document.xml').decode()
 assert action(teacher,dict(action='deleteRecord',id=rid)).status_code==200
 s=state(teacher);assert not any(r['id']==rid for r in s['records']+s['library'])
