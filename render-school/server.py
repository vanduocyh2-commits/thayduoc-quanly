"""Independent school portal for Render. No ChatGPT or Cloudflare dependency."""
import os,json,re,hmac,secrets,hashlib,time,io,unicodedata,zipfile,math
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
from functools import wraps
from flask import Flask,request,jsonify,g,send_from_directory,send_file,make_response
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import create_engine,MetaData,Table,Column,String,Integer,Text,LargeBinary,ForeignKey,UniqueConstraint,select,insert,update,delete,and_,func
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text as sql_text

metadata=MetaData()
members=Table('school_members',metadata,Column('id',String,primary_key=True),Column('username',String,unique=True,nullable=False),Column('password_hash',Text,nullable=False),Column('name',String,nullable=False),Column('email',String),Column('role',String,nullable=False),Column('disabled',Integer,nullable=False,default=0))
courses=Table('school_courses',metadata,Column('id',String,primary_key=True),Column('name',String,nullable=False),Column('subject',String,nullable=False),Column('teacher_id',String,ForeignKey('school_members.id'),nullable=False))
enrollments=Table('school_enrollments',metadata,Column('course_id',String,ForeignKey('school_courses.id'),primary_key=True),Column('member_id',String,ForeignKey('school_members.id'),primary_key=True))
records=Table('school_records',metadata,Column('id',String,primary_key=True),Column('course_id',String,ForeignKey('school_courses.id'),nullable=False),Column('kind',String,nullable=False),Column('author_id',String,ForeignKey('school_members.id'),nullable=False),Column('data',Text,nullable=False),Column('created_at',String,nullable=False))
submissions=Table('school_submissions',metadata,Column('id',String,primary_key=True),Column('assignment_id',String,ForeignKey('school_records.id'),nullable=False),Column('member_id',String,ForeignKey('school_members.id'),nullable=False),Column('data',Text,nullable=False),Column('created_at',String,nullable=False),UniqueConstraint('assignment_id','member_id'))
sessions=Table('school_sessions',metadata,Column('token_hash',String,primary_key=True),Column('member_id',String,ForeignKey('school_members.id'),nullable=False),Column('csrf',String,nullable=False),Column('expires_at',Integer,nullable=False))
limits=Table('school_login_limits',metadata,Column('key',String,primary_key=True),Column('failures',Integer,nullable=False),Column('expires_at',Integer,nullable=False))

library_files=Table('school_library_files',metadata,Column('id',String,primary_key=True),Column('record_id',String,ForeignKey('school_records.id'),unique=True,nullable=False),Column('name',String,nullable=False),Column('mime',String,nullable=False),Column('size',Integer,nullable=False),Column('content',LargeBinary,nullable=False))

rosters=Table('school_rosters',metadata,Column('id',String,primary_key=True),Column('course_id',String,ForeignKey('school_courses.id'),nullable=False),Column('author_id',String,ForeignKey('school_members.id'),nullable=False),Column('data',Text,nullable=False),Column('status',String,nullable=False),Column('created_at',String,nullable=False))

class AppError(Exception):
 def __init__(self,message,status=400):self.message=message;self.status=status

def fail(message,status=400):raise AppError(message,status)
def text(v,maxlen=200,required=True):
 if not isinstance(v,str) or len(v)>maxlen or (required and not v.strip()):fail('Nội dung chưa hợp lệ.')
 return v.strip()
def normalized_short(value,ignore_case=False):
 value=' '.join(value.strip().split())
 if re.fullmatch(r'[+-]?(?:[0-9]+(?:[.,][0-9]+)?|[.,][0-9]+)(?:[eE][+-]?[0-9]+)?',value):value=value.replace(',', '.')
 return value.casefold() if ignore_case else value
def validate_auto_question(q):
 if not isinstance(q,dict):fail('Câu hỏi chưa hợp lệ.')
 text(q.get('text'),2000)
 kind=q.get('type','quiz')
 if kind not in ['quiz','truefalse','short']:fail('Dạng câu hỏi chưa hợp lệ.')
 if kind in ['quiz','truefalse']:
  if not isinstance(q.get('answers'),list) or len(q['answers'])!=4:fail('Cần đủ 4 phương án / ý.')
  for answer in q['answers']:text(answer,1000)
 if kind=='quiz' and (type(q.get('correct')) is not int or not 0<=q['correct']<=3):fail('Chọn đáp án A–D.')
 if kind=='truefalse' and (not isinstance(q.get('correct'),list) or len(q['correct'])!=4 or any(type(v) is not bool for v in q['correct'])):fail('Cần đáp án Đúng / Sai cho đủ 4 ý.')
 if kind=='short':
  text(q.get('correct'),200)
  if type(q.get('ignoreCase',False)) is not bool:fail('Cấu hình trả lời ngắn không hợp lệ.')
def auto_question_score(q,answer,mode,weighted):
 kind=q.get('type','quiz');points=q.get('points',0) if weighted else 1
 if kind=='truefalse':
  if not isinstance(answer,list) or len(answer)!=4 or any(type(v) is not bool for v in answer):fail('Cần trả lời đủ 4 ý Đúng / Sai.')
  right=sum(a==b for a,b in zip(answer,q['correct']))
  return points*(right/4 if mode=='equal' else [0,.1,.25,.5,1][right])
 if kind=='short':
  value=text(answer,200)
  return points if normalized_short(value,q.get('ignoreCase',False))==normalized_short(q['correct'],q.get('ignoreCase',False)) else 0
 if type(answer) is not int or not 0<=answer<=3:fail('Cần chọn đáp án A–D.')
 return points if answer==q['correct'] else 0

def assigned_exam(data,rid,mid):
 variants=data.get('variants',[])
 if not variants:return data
 index=int(hashlib.sha256((rid+':'+mid).encode()).hexdigest(),16)%len(variants)
 v=variants[index]
 return {**data,'questions':v['questions'],'essays':v['essays'],'examCode':v['code']}
def question_signature(q):
 kind=q.get('type','quiz')
 d={k:q.get(k) for k in ['text','points','topic','level','outcome']};d['type']=kind
 if kind=='quiz':d.update(answers=sorted(q['answers']),correct=q['answers'][q['correct']])
 elif kind=='truefalse':d.update(answers=q['answers'],correct=q['correct'])
 elif kind=='short':d.update(correct=q['correct'],ignoreCase=q.get('ignoreCase',False))
 return json.dumps(d,sort_keys=True,ensure_ascii=False)
def validate_variants(data):
 variants=data.get('variants',[])
 if not isinstance(variants,list) or len(variants)>10:fail('Tối đa 10 mã đề.')
 base=Counter(question_signature(q) for q in data['questions']+data.get('essays',[]));codes=set()
 for v in variants:
  if not isinstance(v,dict) or not isinstance(v.get('code'),str) or not re.fullmatch(r'\d{3,4}',v['code']) or v['code'] in codes:fail('Mã đề phải khác nhau, gồm 3–4 chữ số.')
  codes.add(v['code'])
  if not isinstance(v.get('questions'),list) or not isinstance(v.get('essays'),list) or len(v['questions'])!=len(data['questions']) or len(v['essays'])!=len(data.get('essays',[])):fail('Mã đề phải giữ đủ câu của đề gốc.')
  for q in v['questions']:validate_auto_question(q)
  for q in v['essays']:
   if not isinstance(q,dict) or q.get('type')!='essay':fail('Câu tự luận trong mã đề chưa hợp lệ.')
  try:valid=Counter(question_signature(q) for q in v['questions']+v['essays'])==base
  except (TypeError,KeyError,IndexError):valid=False
  if not valid:fail('Bản đảo phải giữ nguyên nội dung, thang điểm và đáp án đúng của đề gốc.')

def validate_exam_data(d):
 if d.get('type') not in ['essay','quiz','mixed']:fail('Hình thức chưa hợp lệ.')
 if d.get('due'):parse_date(d['due'])
 if d['type'] in ['quiz','mixed']:
  qs=d.get('questions')
  if not isinstance(qs,list) or not 1<=len(qs)<=100:fail('Cần từ 1 đến 100 câu hỏi.')
  for q in qs:validate_auto_question(q)
 else:d['questions']=[]
 essays=d.get('essays',[])
 if not isinstance(essays,list) or len(essays)>100:fail('Tối đa 100 câu tự luận.')
 for q in essays:
  if not isinstance(q,dict):fail('Câu tự luận chưa hợp lệ.')
  text(q.get('text'),2000)
  q['type']='essay'
 if d['type']=='mixed' and not essays:fail('Đề kết hợp cần câu tự luận.')
 if d.get('composed'):
  all_q=d['questions']+essays
  if not 1<=len(all_q)<=100:fail('Đề cần từ 1 đến 100 câu hỏi.')
  for q in all_q:
   if type(q.get('points')) not in [int,float] or not math.isfinite(q['points']) or not 0<q['points']<=10:fail('Điểm câu hỏi phải lớn hơn 0 và không quá 10.')
   q['topic']=text(q.get('topic'),200);q['level']=text(q.get('level'),100)
   q['outcome']=text(q.get('outcome',''),2000,False)
   if q['level'] not in ['Nhận biết','Thông hiểu','Vận dụng','Vận dụng cao']:fail('Mức độ không hợp lệ.')
  if abs(sum(q['points'] for q in all_q)-10)>0.001:fail('Tổng điểm đề phải bằng 10.')
 if d.get('minutes') is not None and (type(d['minutes']) is not int or not 1<=d['minutes']<=300):fail('Thời gian cần từ 1 đến 300 phút.')
 if d.get('grade') is not None and str(d['grade']) not in [str(i) for i in range(1,13)]:fail('Khối lớp không hợp lệ.')
 if d.get('tfScoring','progressive') not in ['progressive','equal']:fail('Cách chấm Đúng / Sai không hợp lệ.')
 d['includeMatrix']=bool(d.get('includeMatrix',False))
 validate_variants(d)
 if d.get('subjectCode') is not None and not re.fullmatch(r'\d{2}',str(d['subjectCode'])):fail('Mã môn cần đúng 2 chữ số.')
 d.pop('file',None)

def password(v):
 if not isinstance(v,str) or not 10<=len(v)<=200:fail('Mật khẩu cần từ 10 đến 200 ký tự.')
 return generate_password_hash(v)
def username(v):
 v=text(v,60).lower()
 if not re.fullmatch(r'[a-z0-9_.-]{3,60}',v):fail('Tên đăng nhập cần 3–60 chữ không dấu, số, dấu chấm, gạch dưới hoặc gạch nối.')
 return v
def uid():return secrets.token_hex(16)
def now():return datetime.now(timezone.utc).isoformat()
def parse_date(value):
 try:return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
 except (ValueError,AttributeError,TypeError):fail('Ngày giờ chưa hợp lệ.')
def may_teach(m,c):return not m['disabled'] and (m['role']=='admin' or (m['role']=='teacher' and c['teacher_id']==m['id']))
def public_member(m):return {k:v for k,v in m.items() if k!='password_hash'}

def normalized(v):return ''.join(c for c in unicodedata.normalize('NFD',str(v).lower().replace('đ','d')) if not unicodedata.combining(c)).strip()
def roster_students(values):
 if not isinstance(values,list) or not 1<=len(values)<=500:fail('Danh sách cần từ 1 đến 500 học sinh.')
 result=[];seen=set()
 for i,v in enumerate(values,1):
  if not isinstance(v,dict):fail('Dòng học sinh chưa hợp lệ.')
  code=username(v.get('code'));name=text(v.get('name'),200)
  if code in seen:fail(f'Dòng {i}: trùng mã học sinh {code}.')
  seen.add(code);result.append({'code':code,'name':name})
 return result

def parse_roster(upload):
 from openpyxl import load_workbook
 if not upload:fail('Hãy chọn file Excel .xlsx.')
 if not upload.filename.lower().endswith('.xlsx'):fail('Hỗ trợ Excel .xlsx. Với file .xls, hãy lưu thành .xlsx trước.')
 raw=upload.read()
 try:
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   if sum(x.file_size for x in z.infolist())>40*1024*1024:fail('File Excel sau giải nén quá lớn.')
  wb=load_workbook(io.BytesIO(raw),read_only=True,data_only=True)
 except AppError:raise
 except Exception:fail('Không đọc được file Excel. Hãy kiểm tra file .xlsx không có mật khẩu.')
 result=[];errors=[];seen=set();found=False
 try:
  for sheet in wb:
   header=None
   for line,row in enumerate(sheet.iter_rows(max_row=min(sheet.max_row or 0,2000),max_col=50,values_only=True),1):
    cells=[normalized(v or '') for v in row]
    if header is None:
     code=next((i for i,v in enumerate(cells) if v in ['ma hoc sinh','ma hs','ma dinh danh bo gd&dt','ma dinh danh','sbd','ten dang nhap']),None)
     name=next((i for i,v in enumerate(cells) if v in ['ho va ten','ho ten','ho va ten hoc sinh']),None)
     if code is not None and name is not None:header=(code,name);found=True
     continue
    code_value=row[header[0]];name_value=row[header[1]]
    if not code_value and not name_value:continue
    # Skip the second header line and footer summaries in Ministry grade exports.
    if not code_value and (not row[0] or not str(row[0]).strip().isdigit()):continue
    code=str(int(code_value)) if isinstance(code_value,(int,float)) and float(code_value).is_integer() else str(code_value or '').strip()
    try:
     item=roster_students([{'code':code,'name':str(name_value or '')}])[0]
     if item['code'] in seen:fail('Trùng mã học sinh trong file.')
     seen.add(item['code']);result.append(item)
    except AppError as e:errors.append(f'{sheet.title}, dòng {line}: {e.message}')
    if len(result)>500:fail('Mỗi lần tải tối đa 500 học sinh.')
   if header and (sheet.max_row or 0)>2000:errors.append(f'{sheet.title}: bảng vượt quá 2000 dòng, hãy tách file.')
 finally:wb.close()
 if not found:fail('Không tìm thấy cột Mã định danh Bộ GD&ĐT / Mã học sinh và Họ và tên trong 50 cột đầu.')
 if not result and not errors:fail('Không có học sinh trong file.')
 return result,errors

def create_app(config=None):
 app=Flask(__name__,static_folder='static',static_url_path='/static');app.config.update(MAX_CONTENT_LENGTH=6*1024*1024,SECRET_KEY=os.getenv('SECRET_KEY'),DATABASE_URL=os.getenv('DATABASE_URL'),ADMIN_SETUP_TOKEN=os.getenv('ADMIN_SETUP_TOKEN'),SESSION_SECONDS=43200,TESTING=False)
 if config:app.config.update(config)
 if not app.config['SECRET_KEY'] or len(app.config['SECRET_KEY'])<32:raise RuntimeError('Configure SECRET_KEY (at least 32 characters).')
 url=app.config['DATABASE_URL']
 if not url:raise RuntimeError('Configure DATABASE_URL for a separate persistent school database.')
 if url.startswith('postgres://'):url='postgresql+psycopg://'+url[len('postgres://'):]
 elif url.startswith('postgresql://'):url='postgresql+psycopg://'+url[len('postgresql://'):]
 engine=create_engine(url,pool_pre_ping=True,**({'connect_args':{'check_same_thread':False}} if url.startswith('sqlite') else {'pool_size':5,'max_overflow':5}))
 app.extensions['school_engine']=engine
 if engine.dialect.name=='postgresql':
  with engine.begin() as conn:
   conn.execute(sql_text('SELECT pg_advisory_xact_lock(719246830)'))
   metadata.create_all(conn)
   for table in metadata.sorted_tables:
    conn.execute(sql_text(f'ALTER TABLE {table.name} ENABLE ROW LEVEL SECURITY'))
    conn.execute(sql_text(f'REVOKE ALL ON TABLE {table.name} FROM PUBLIC'))
 else:metadata.create_all(engine)
 app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1,x_host=0)
 cookie='school_session'
 def one(table,where):return g.db.execute(select(table).where(where)).mappings().first()
 def rows(table):return [dict(x) for x in g.db.execute(select(table)).mappings()]
 def origin():
  if request.headers.get('Origin')!=request.host_url.rstrip('/'):fail('Nguồn yêu cầu không hợp lệ.',403)
 def body():
  if not request.is_json:fail('Yêu cầu JSON.',415)
  p=request.get_json(silent=True)
  if not isinstance(p,dict):fail('Nội dung chưa hợp lệ.')
  return p
 def admin():
  if g.member['role']!='admin':fail('Chỉ quản trị viên được thao tác.',403)
 def get_course(cid):
  c=one(courses,courses.c.id==text(cid))
  if not c:fail('Không tìm thấy lớp / môn.',404)
  return c
 def teach(cid):
  c=get_course(cid)
  if not may_teach(g.member,c):fail('Bạn không được phân công lớp / môn này.',403)
  return c
 def read(cid):
  c=get_course(cid)
  if not may_teach(g.member,c) and not (g.member['role']=='student' and one(enrollments,and_(enrollments.c.course_id==cid,enrollments.c.member_id==g.member['id']))):fail('Bạn không thuộc lớp / môn này.',403)
  return c
 def require_member():
  if not g.member:fail('Bạn cần đăng nhập.',401)
 def ratekeys(user):
  return [('ip:'+request.remote_addr,30),('user:'+user,10)]
 def check_rate(user):
  for key,threshold in ratekeys(user):
   r=one(limits,limits.c.key==hashlib.sha256(key.encode()).hexdigest())
   if r and r['expires_at']>int(time.time()) and r['failures']>=threshold:fail('Thử đăng nhập quá nhiều lần. Vui lòng chờ 15 phút.',429)
 def record_failure(user):
  # Atomic increment for both PostgreSQL and SQLite, including concurrent workers.
  for key,_ in ratekeys(user):
   key=hashlib.sha256(key.encode()).hexdigest();ts=int(time.time());r=one(limits,limits.c.key==key)
   if r and r['expires_at']>ts:g.db.execute(update(limits).where(limits.c.key==key).values(failures=limits.c.failures+1))
   elif r:g.db.execute(update(limits).where(limits.c.key==key).values(failures=1,expires_at=ts+900))
   else:
    dialect=engine.dialect.name
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sq_insert
    ins=(pg_insert if dialect=='postgresql' else sq_insert)(limits).values(key=key,failures=1,expires_at=ts+900)
    g.db.execute(ins.on_conflict_do_update(index_elements=['key'],set_={'failures':limits.c.failures+1}))
  g.db.commit()
 def sign_in(m):
  token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(32);ts=int(time.time())
  g.db.execute(delete(sessions).where(sessions.c.expires_at<ts));g.db.execute(insert(sessions).values(token_hash=hashlib.sha256(token.encode()).hexdigest(),member_id=m['id'],csrf=csrf,expires_at=ts+app.config['SESSION_SECONDS']))
  res=jsonify(ok=True);res.set_cookie(cookie,token,httponly=True,secure=not app.config['TESTING'],samesite='Lax',max_age=app.config['SESSION_SECONDS'],path='/');return res
 @app.before_request
 def before():
  if not request.path.startswith('/api/') and request.path!='/healthz':return
  g.db=engine.connect();g.member=None;g.auth=None
  if request.path in ['/api/school','/api/login','/api/setup'] and (request.content_length or 0)>160000:fail('Nội dung quá lớn.',413)
  token=request.cookies.get(cookie)
  if token:
   sess=one(sessions,and_(sessions.c.token_hash==hashlib.sha256(token.encode()).hexdigest(),sessions.c.expires_at>int(time.time())))
   if sess:
    m=one(members,and_(members.c.id==sess['member_id'],members.c.disabled==0))
    if m:g.member=m;g.auth=sess
  if request.method=='POST':
   origin()
   if request.path not in ['/api/login','/api/setup']:
    require_member()
    if not hmac.compare_digest(request.headers.get('X-CSRF-Token',''),g.auth['csrf']):fail('Phiên xác thực không hợp lệ. Hãy tải lại trang.',403)
 @app.after_request
 def after(res):
  if hasattr(g,'db'):
   if res.status_code<400:g.db.commit()
   else:g.db.rollback()
  res.headers['X-Content-Type-Options']='nosniff';res.headers['Referrer-Policy']='same-origin';res.headers['X-Frame-Options']='DENY'
  res.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
  if request.path.startswith('/api/'):res.headers['Cache-Control']='no-store'
  return res
 @app.teardown_request
 def close(_):
  if hasattr(g,'db'):g.db.close()
 @app.errorhandler(AppError)
 def app_error(e):return jsonify(error=e.message),e.status
 @app.errorhandler(IntegrityError)
 def conflict(_):return jsonify(error='Tên đăng nhập, ghi danh hoặc bài nộp đã tồn tại.'),409
 @app.errorhandler(413)
 def too_large(_):return jsonify(error='Nội dung quá lớn.'),413
 @app.errorhandler(500)
 def generic(_):return jsonify(error='Máy chủ gặp lỗi. Vui lòng thử lại.'),500
 @app.get('/healthz')
 def health():g.db.execute(select(1));return jsonify(status='ok')
 @app.get('/api/auth')
 def auth():return jsonify(csrf=g.auth['csrf'] if g.auth else '',setupNeeded=not bool(one(members,members.c.role=='admin')))
 @app.post('/api/setup')
 def setup():
  if one(members,members.c.role=='admin'):fail('Quản trị viên đã được thiết lập.',409)
  p=body();check_rate('setup');expected=app.config.get('ADMIN_SETUP_TOKEN') or ''
  if len(expected)<24 or not hmac.compare_digest(str(p.get('setupToken','')),expected):record_failure('setup');fail('Mã thiết lập không đúng.',403)
  m={'id':'school-owner','username':username(p.get('username')),'password_hash':password(p.get('password')),'name':text(p.get('name')),'email':None,'role':'admin','disabled':0};g.db.execute(insert(members).values(**m));return sign_in(m)
 @app.post('/api/login')
 def login():
  p=body();u=str(p.get('username','')).strip().lower()[:200];check_rate(u);m=one(members,members.c.username==u)
  supplied=p.get('password','');valid=isinstance(supplied,str) and len(supplied)<=200
  if not m or m['disabled'] or not valid or not check_password_hash(m['password_hash'],supplied):record_failure(u);fail('Tên đăng nhập hoặc mật khẩu không đúng.',401)
  g.db.execute(delete(limits).where(limits.c.key==hashlib.sha256(('user:'+u).encode()).hexdigest()));return sign_in(m)
 @app.post('/api/logout')
 def logout():
  g.db.execute(delete(sessions).where(sessions.c.token_hash==g.auth['token_hash']));r=jsonify(ok=True);r.delete_cookie(cookie,path='/');return r
 @app.get('/api/school')
 def snapshot():
  require_member();m=g.member;all_es=rows(enrollments);all_cs=rows(courses);cs=[c for c in all_cs if may_teach(m,c) or (m['role']=='student' and any(e['course_id']==c['id'] and e['member_id']==m['id'] for e in all_es))];ids={c['id'] for c in cs};es=[e for e in all_es if e['course_id'] in ids and (m['role']!='student' or e['member_id']==m['id'])]
  all_ms=rows(members);ms=all_ms
  if m['role']!='admin':ms=[x for x in ms if x['id']==m['id'] or any(c['teacher_id']==x['id'] for c in cs) or (m['role']=='teacher' and any(e['member_id']==x['id'] for e in es))]
  ms=[public_member(x) for x in ms]
  if m['role']!='admin':ms=[{k:v for k,v in x.items() if k not in ['email','username'] or x['id']==m['id']} for x in ms]
  all_rs=rows(records);rs=[]
  for r in sorted(all_rs,key=lambda x:x['created_at'],reverse=True):
   if r['kind']=='library' or r['course_id'] not in ids:continue
   c=next(c for c in cs if c['id']==r['course_id']);d=json.loads(r['data'])
   if not may_teach(m,c):
    if r['kind'] in ['attendance','grade','message'] and d.get('memberId') not in [m['id'],'all'] and r['author_id']!=m['id']:continue
    if r['kind']=='assignment':
     d=assigned_exam(d,r['id'],m['id']);d.pop('variants',None)
     d.pop('answerNotes',None)
     for field in ['questions','essays']:d[field]=[{k:v for k,v in q.items() if k not in ['correct','outcome']} for q in d.get(field,[])]
   rs.append({**r,'data':d})
  ss=[]
  for sub in rows(submissions):
   a=next((r for r in all_rs if r['id']==sub['assignment_id']),None)
   if a and a['course_id'] in ids and (m['role']!='student' or sub['member_id']==m['id']):ss.append({**sub,'data':json.loads(sub['data'])})
  lib=[]
  for r in sorted(all_rs,key=lambda x:x['created_at'],reverse=True):
   if r['kind']!='library':continue
   d=json.loads(r['data'])
   if m['role']=='student' and (r['course_id'] not in ids or not d.get('published')):continue
   c=next((c for c in all_cs if c['id']==r['course_id']),None)
   lib.append({**r,'data':d,'course_label':(c['name']+' · '+c['subject']) if c else 'Lớp / môn đã xóa','author_name':next((x['name'] for x in all_ms if x['id']==r['author_id']),'Giáo viên')})
  return jsonify(me=public_member(dict(m)),members=ms,courses=cs,enrollments=es,records=rs,submissions=ss,library=lib,rosters=[{**r,'data':json.loads(r['data'])} for r in rows(rosters) if m['role']=='admin' or (m['role']=='teacher' and r['author_id']==m['id'] and r['course_id'] in ids)])
 @app.post('/api/student-roster/preview')
 def preview_roster():
  teach(text(request.form.get('courseId')))
  students,errors=parse_roster(request.files.get('file'))
  return jsonify(students=students,errors=errors)
 @app.get('/api/student-roster/template')
 def roster_template():
  require_member()
  if g.member['role'] not in ['admin','teacher']:fail('Chỉ giáo viên và quản trị viên.',403)
  from openpyxl import Workbook
  w=Workbook();sheet=w.active;sheet.title='Danh sach hoc sinh'
  sheet.append(['STT','Mã định danh Bộ GD&ĐT','Họ và tên'])
  sheet.append([1,'HS001','Nguyễn Văn A']);sheet.cell(2,2).number_format='@'
  sheet.column_dimensions['B'].width=30;sheet.column_dimensions['C'].width=35
  out=io.BytesIO();w.save(out);out.seek(0)
  return send_file(out,as_attachment=True,download_name='mau-danh-sach-hoc-sinh.xlsx')
 @app.post('/api/school')
 @app.post('/api/exams')
 def action():
  if request.path=='/api/exams':
   try:p=json.loads(request.form.get('payload','{}'))
   except Exception:fail('Dữ liệu đề không hợp lệ.')
   if not isinstance(p,dict) or p.get('action')!='record' or p.get('kind')!='assignment':fail('Yêu cầu tạo đề chưa hợp lệ.')
  else:p=body()
  a=p.get('action');m=g.member
  if a=='submitRoster':
   cid=text(p.get('courseId'));teach(cid);students=roster_students(p.get('students'))
   g.db.execute(insert(rosters).values(id=uid(),course_id=cid,author_id=m['id'],data=json.dumps(students,ensure_ascii=False),status='pending',created_at=now()))
  elif a in ['approveRoster','rejectRoster']:
   admin();rid=text(p.get('id'));r=g.db.execute(select(rosters).where(rosters.c.id==rid).with_for_update()).mappings().first()
   if not r or r['status']!='pending':fail('Danh sách đã được xử lý hoặc không tồn tại.',409)
   get_course(r['course_id']);credentials=[]
   if a=='approveRoster':
    for st in roster_students(json.loads(r['data'])):
     existing=one(members,members.c.username==st['code'])
     if existing:
      if existing['role']!='student' or existing['disabled'] or normalized(existing['name'])!=normalized(st['name']):fail(f"Mã {st['code']} đã thuộc tài khoản khác hoặc bị khóa. Hãy kiểm tra trước khi duyệt.",409)
      mid=existing['id'];pw='';note='Tài khoản đã có: giữ mật khẩu hiện tại'
     else:
      mid=uid();pw=secrets.token_urlsafe(12);note='Tài khoản mới'
      g.db.execute(insert(members).values(id=mid,username=st['code'],password_hash=password(pw),name=st['name'],email='',role='student',disabled=0))
     where=and_(enrollments.c.course_id==r['course_id'],enrollments.c.member_id==mid)
     if not one(enrollments,where):g.db.execute(insert(enrollments).values(course_id=r['course_id'],member_id=mid))
     credentials.append({'name':st['name'],'username':st['code'],'password':pw,'note':note})
   g.db.execute(update(rosters).where(rosters.c.id==rid).values(status='approved' if a=='approveRoster' else 'rejected'))
   return jsonify(ok=True,credentials=credentials)
  elif a=='member':
   admin();role=p.get('role')
   if role not in ['teacher','student']:fail('Vai trò chưa hợp lệ.')
   g.db.execute(insert(members).values(id=uid(),username=username(p.get('username')),password_hash=password(p.get('password')),name=text(p.get('name')),email=text(p.get('email',''),200,False),role=role,disabled=0))
  elif a=='toggleMember':
   admin();x=one(members,members.c.id==text(p.get('id')))
   if not x or x['role']=='admin':fail('Không thể khóa quản trị viên.')
   g.db.execute(update(members).where(members.c.id==x['id']).values(disabled=0 if x['disabled'] else 1));g.db.execute(delete(sessions).where(sessions.c.member_id==x['id']))
  elif a in ['password','resetPassword']:
   if a=='resetPassword':
    admin();target=text(p.get('id'));x=one(members,members.c.id==target)
    if not x or x['role']=='admin':fail('Hãy dùng mục đổi mật khẩu của tôi cho quản trị viên.')
   else:
    target=m['id']
    if not isinstance(p.get('oldPassword'),str) or not check_password_hash(m['password_hash'],p['oldPassword']):fail('Mật khẩu hiện tại chưa đúng.')
   g.db.execute(update(members).where(members.c.id==target).values(password_hash=password(p.get('password'))));g.db.execute(delete(sessions).where(sessions.c.member_id==target))
  elif a=='course':
   admin();tid=text(p.get('teacherId'));t=one(members,and_(members.c.id==tid,members.c.role=='teacher',members.c.disabled==0))
   if not t:fail('Chọn giáo viên đang hoạt động.')
   values={'name':text(p.get('name')),'subject':text(p.get('subject')),'teacher_id':tid}
   if p.get('id'):get_course(p['id']);g.db.execute(update(courses).where(courses.c.id==p['id']).values(**values))
   else:g.db.execute(insert(courses).values(id=uid(),**values))
  elif a=='enroll':
   admin();cid=text(p.get('courseId'));get_course(cid);mid=text(p.get('memberId'));x=one(members,and_(members.c.id==mid,members.c.role=='student',members.c.disabled==0))
   if not x:fail('Chọn học sinh đang hoạt động.')
   where=and_(enrollments.c.course_id==cid,enrollments.c.member_id==mid)
   if p.get('remove'):g.db.execute(delete(enrollments).where(where))
   elif not one(enrollments,where):g.db.execute(insert(enrollments).values(course_id=cid,member_id=mid))
  elif a=='record':
   cid=text(p.get('courseId'));kind=p.get('kind');d=p.get('data')
   if kind not in ['assignment','lesson','schedule','attendance','grade','message'] or not isinstance(d,dict):fail('Dữ liệu chưa hợp lệ.')
   if kind=='message' and m['role']=='student':read(cid);d['memberId']=m['id'];d['read']=False
   else:teach(cid)
   if kind in ['assignment','lesson','schedule','grade','message']:d['title']=text(d.get('title'))
   if kind in ['lesson','assignment','message']:d['body']=text(d.get('body'),20000 if kind!='message' else 4000)
   if d.get('url') and not re.match(r'^https?://',str(d['url']),re.I):fail('Liên kết không hợp lệ.')
   if kind=='assignment':
    validate_exam_data(d);d['subject']=get_course(cid)['subject']
   if kind=='schedule':parse_date(d.get('at'));d['room']=text(d.get('room'))
   if kind in ['grade','attendance'] or (kind=='message' and m['role']!='student' and d.get('memberId')!='all'):
    mid=text(d.get('memberId'))
    if not one(enrollments,and_(enrollments.c.course_id==cid,enrollments.c.member_id==mid)):fail('Học sinh không thuộc lớp / môn này.')
   if kind=='grade' and (type(d.get('score')) not in [int,float] or not 0<=d['score']<=10):fail('Điểm từ 0 đến 10.')
   if kind=='attendance':
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',str(d.get('date'))) or d.get('status') not in ['Có mặt','Vắng có phép','Vắng không phép','Đi muộn','Học bù']:fail('Điểm danh chưa hợp lệ.')
    prev=next((r for r in rows(records) if r['course_id']==cid and r['kind']=='attendance' and json.loads(r['data']).get('memberId')==d['memberId'] and json.loads(r['data']).get('date')==d['date']),None)
    if prev:g.db.execute(update(records).where(records.c.id==prev['id']).values(data=json.dumps(d,ensure_ascii=False)));return jsonify(ok=True)
   if kind=='message':d['read']=False
   rid=uid();file_data=None
   if request.path=='/api/exams':
    file=request.files.get('file')
    if file and file.filename:
     content=file.stream.read(5*1024*1024+1)
     if not file.filename.lower().endswith('.pdf') or not content.startswith(b'%PDF-') or len(content)>5*1024*1024:fail('Chọn tệp PDF hợp lệ, tối đa 5 MB.')
     if engine.dialect.name=='postgresql':g.db.execute(sql_text('SELECT pg_advisory_xact_lock(719246831)'))
     used=g.db.execute(select(func.coalesce(func.sum(library_files.c.size),0))).scalar_one()
     if used+len(content)>250*1024*1024:fail('Kho tệp đã đạt 250 MB.')
     name=secure_filename(file.filename) or 'de-thi.pdf'
     file_data=dict(id=uid(),record_id=rid,name=name,mime='application/pdf',size=len(content),content=content)
     d['file']={'name':name,'url':'/api/exams/'+rid+'/file'}
   g.db.execute(insert(records).values(id=rid,course_id=cid,kind=kind,author_id=m['id'],data=json.dumps(d,ensure_ascii=False),created_at=now()))
   if file_data:g.db.execute(insert(library_files).values(**file_data))
  elif a=='submit':
   if m['role']!='student':fail('Chỉ học sinh được nộp bài.',403)
   r=one(records,and_(records.c.id==text(p.get('assignmentId')),records.c.kind=='assignment'))
   if not r:fail('Không tìm thấy bài tập.',404)
   read(r['course_id']);d=assigned_exam(json.loads(r['data']),r['id'],m['id'])
   if d.get('due') and time.time()>parse_date(d['due']):fail('Đã hết hạn nộp.')
   if d['type'] in ['quiz','mixed']:
    ans=p.get('answers');qs=d['questions']
    if not isinstance(ans,list) or len(ans)!=len(qs):fail('Cần trả lời đầy đủ các câu hỏi.')
    earned=sum(auto_question_score(q,ans[i],d.get('tfScoring','progressive'),bool(d.get('composed'))) for i,q in enumerate(qs))
    score=round(earned if d.get('composed') else earned/len(qs)*10,2)
    data={'answers':ans,'score':score,'feedback':''}
    if d['type']=='mixed':data.update(text=text(p.get('text'),30000),quizScore=data['score'],score=None)
   else:data={'text':text(p.get('text'),30000),'score':None,'feedback':''}
   if d.get('examCode'):data['examCode']=d['examCode']
   g.db.execute(insert(submissions).values(id=uid(),assignment_id=r['id'],member_id=m['id'],data=json.dumps(data,ensure_ascii=False),created_at=now()))
  elif a=='grade':
   sub=one(submissions,submissions.c.id==text(p.get('id')))
   if not sub:fail('Không tìm thấy bài nộp.',404)
   r=one(records,records.c.id==sub['assignment_id']);teach(r['course_id']);score=p.get('score')
   if type(score) not in [int,float] or not 0<=score<=10:fail('Điểm từ 0 đến 10.')
   d=json.loads(sub['data']);d.update(score=score,feedback=text(p.get('feedback',''),4000,False));g.db.execute(update(submissions).where(submissions.c.id==sub['id']).values(data=json.dumps(d,ensure_ascii=False)))
  elif a=='readMessage':
   r=one(records,and_(records.c.id==text(p.get('id')),records.c.kind=='message'))
   if not r:fail('Không tìm thấy trao đổi.')
   c=read(r['course_id']);d=json.loads(r['data'])
   if may_teach(m,c) and r['author_id']!=m['id']:d['read']=True
   elif m['role']=='student' and d.get('memberId') in [m['id'],'all'] and r['author_id']!=m['id']:d['readBy']=list(set(d.get('readBy',[])+[m['id']]))
   else:fail('Bạn không phải người nhận.',403)
   g.db.execute(update(records).where(records.c.id==r['id']).values(data=json.dumps(d,ensure_ascii=False)))
  elif a=='deleteRecord':
   r=one(records,records.c.id==text(p.get('id')))
   if not r:fail('Không tìm thấy nội dung.')
   if r['kind']=='library':
    if m['role']!='admin' and (m['role']!='teacher' or r['author_id']!=m['id']):fail('Chỉ người đăng hoặc quản trị viên được xóa tài liệu.',403)
    g.db.execute(delete(library_files).where(library_files.c.record_id==r['id']))
   else:teach(r['course_id'])
   g.db.execute(delete(library_files).where(library_files.c.record_id==r['id']))
   g.db.execute(delete(submissions).where(submissions.c.assignment_id==r['id']));g.db.execute(delete(records).where(records.c.id==r['id']))
  else:fail('Thao tác chưa hợp lệ.')
  return jsonify(ok=True)
 @app.post('/api/library')
 def save_library():
  if g.member['role'] not in ['admin','teacher']:fail('Chỉ giáo viên và quản trị viên được đăng tài liệu.',403)
  f=request.form;rid=f.get('id') or uid();existing=one(records,records.c.id==rid)
  if existing and (existing['kind']!='library' or (g.member['role']!='admin' and existing['author_id']!=g.member['id'])):fail('Bạn không được sửa tài liệu này.',403)
  cid=text(f.get('courseId'));c=teach(cid);category=f.get('category');grade=f.get('grade','')
  if category not in ['lesson','exam'] or grade not in [str(i) for i in range(1,13)]+['other']:fail('Chọn loại tài liệu và khối lớp hợp lệ.')
  d={'title':text(f.get('title')), 'body':text(f.get('body',''),10000,False),'url':text(f.get('url',''),2000,False),'category':category,'grade':grade,'subject':c['subject'],'published':f.get('published')=='true'}
  if d['url'] and not re.match(r'^https?://',d['url'],re.I):fail('Liên kết cần bắt đầu bằng http:// hoặc https://.')
  if existing:d['file']=json.loads(existing['data']).get('file')
  file=request.files.get('file');file_data=None
  if file and file.filename:
   name=secure_filename(file.filename) or 'tai-lieu';ext=Path(name).suffix.lower();allowed={'.pdf':'application/pdf','.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','.xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','.txt':'text/plain','.md':'text/markdown','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg'}
   if ext not in allowed:fail('Hỗ trợ PDF, DOCX, XLSX, TXT, MD và ảnh PNG/JPG.')
   content=file.stream.read(5*1024*1024+1)
   if not content or len(content)>5*1024*1024:fail('Tệp cần có nội dung và không vượt quá 5 MB.')
   file_data={'id':uid(),'record_id':rid,'name':name,'mime':allowed[ext],'size':len(content),'content':content}
   if engine.dialect.name=='postgresql':g.db.execute(sql_text('SELECT pg_advisory_xact_lock(719246831)'))
   used=g.db.execute(select(func.coalesce(func.sum(library_files.c.size),0))).scalar_one();old_size=g.db.execute(select(library_files.c.size).where(library_files.c.record_id==rid)).scalar_one_or_none() or 0
   if used-old_size+len(content)>250*1024*1024:fail('Thư viện đã đạt hạn mức tệp 250 MB. Hãy xóa tệp cũ hoặc dùng liên kết.')
   d['file']={'name':name,'size':len(content),'url':'/api/library/'+rid+'/file'}
  elif f.get('removeFile')=='true':d['file']=None
  if not d['body'] and not d['url'] and not d.get('file'):fail('Cần nội dung, liên kết hoặc tệp tài liệu.')
  values={'course_id':cid,'data':json.dumps(d,ensure_ascii=False)}
  if existing:g.db.execute(update(records).where(records.c.id==rid).values(**values))
  else:g.db.execute(insert(records).values(id=rid,kind='library',author_id=g.member['id'],created_at=now(),**values))
  if file_data or f.get('removeFile')=='true':g.db.execute(delete(library_files).where(library_files.c.record_id==rid))
  if file_data:g.db.execute(insert(library_files).values(**file_data))
  return jsonify(ok=True,id=rid)
 @app.get('/api/library/<rid>/file')
 def download_library(rid):
  require_member();r=one(records,and_(records.c.id==rid,records.c.kind=='library'))
  if not r:fail('Không tìm thấy tài liệu.',404)
  d=json.loads(r['data'])
  if g.member['role']=='student':
   if not d.get('published'):fail('Tài liệu chưa được xuất bản.',403)
   read(r['course_id'])
  f=one(library_files,library_files.c.record_id==rid)
  if not f:fail('Không tìm thấy tệp.',404)
  return send_file(io.BytesIO(f['content']),mimetype=f['mime'],download_name=f['name'],as_attachment=True,max_age=0)
 @app.post('/api/exams/export')
 def export_exam():
  from exam_export import export_pack,outline_doc
  p=body();c=teach(text(p.get('courseId')));d=p.get('data')
  if not isinstance(d,dict) or not d.get('composed'):fail('Cần đề soạn trực tiếp để xuất tệp.')
  d['title']=text(d.get('title'));d['body']=text(d.get('body',''),12000,False)
  validate_exam_data(d);d['subject']=c['subject']
  if p.get('format')=='outline':return send_file(io.BytesIO(outline_doc(d)),mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',as_attachment=True,download_name='de-cuong.docx')
  return send_file(io.BytesIO(export_pack(d)),mimetype='application/zip',as_attachment=True,download_name='bo-de-kiem-tra.zip')
 @app.get('/api/exams/<rid>/file')
 def exam_file(rid):
  require_member();r=one(records,and_(records.c.id==rid,records.c.kind=='assignment'))
  if not r:fail('Không tìm thấy đề.',404)
  read(r['course_id']);f=one(library_files,library_files.c.record_id==rid)
  if not f:fail('Không tìm thấy PDF.',404)
  return send_file(io.BytesIO(f['content']),mimetype='application/pdf',download_name=f['name'],as_attachment=True,max_age=0)
 @app.get('/')
 def index():return send_from_directory(app.static_folder,'index.html')
 @app.get('/assets/<path:name>')
 def assets(name):return send_from_directory(Path(app.static_folder)/'assets',name,max_age=31536000)
 return app
