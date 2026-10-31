"""Assignment reminders, generated once per pupil, recipient and scheduled event."""
import hashlib,json,math,time
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select,insert,update,text as sql_text

def normalize_reminder(value,start=None,end=None,bank_only=False):
 if value is None:return dict(enabled=False,beforeStart=False,beforeEnd=True,hours=2,students=True,parents=True)
 keys=['enabled','beforeStart','beforeEnd','students','parents']
 if not isinstance(value,dict) or any(type(value.get(k)) is not bool for k in keys) or type(value.get('hours')) not in [int,float] or not math.isfinite(value['hours']) or not .25<=value['hours']<=168:raise ValueError('Hẹn giờ nhắc: chọn từ 0,25 đến 168 giờ và người nhận.')
 r={k:value[k] for k in keys+['hours']}
 if r['enabled']:
  if not(r['beforeStart'] or r['beforeEnd']) or not(r['students'] or r['parents']):raise ValueError('Chọn thời điểm nhắc và ít nhất một người nhận.')
  if not bank_only and ((r['beforeStart'] and not start) or (r['beforeEnd'] and not end)):raise ValueError('Hãy đặt giờ mở đề / hạn nộp tương ứng trước khi bật nhắc.')
 return r

def process_reminders(db,records,courses,enrollments,members,submissions,now=None):
 ts=time.time() if now is None else now;sent=0
 if db.dialect.name=='postgresql':db.execute(sql_text('SELECT pg_advisory_xact_lock(719246852)'))
 all_courses={c['id']:c for c in db.execute(select(courses)).mappings()};all_members={m['id']:m for m in db.execute(select(members)).mappings()}
 enrolled=list(db.execute(select(enrollments)).mappings());submitted={(s['assignment_id'],s['member_id']) for s in db.execute(select(submissions.c.assignment_id,submissions.c.member_id)).mappings()}
 assignments=list(db.execute(select(records.c.id).where(records.c.kind=='assignment')).scalars())
 for rid in assignments:
  row=db.execute(select(records).where(records.c.id==rid).with_for_update()).mappings().first()
  if not row:continue
  d=json.loads(row['data']);r=d.get('reminder',{});c=all_courses.get(row['course_id'])
  if not r.get('enabled') or d.get('bankOnly') or d.get('bankArchivedAt') or d.get('closedAt') or not c:continue
  seen=set(d.get('_reminderSent',[]));before=len(seen)
  for kind,anchor,enabled in [('start',d.get('opensAt'),r.get('beforeStart')),('end',d.get('due'),r.get('beforeEnd'))]:
   if not enabled or not anchor:continue
   try:target=datetime.fromisoformat(anchor.replace('Z','+00:00')).timestamp()
   except (ValueError,TypeError):continue
   if not target-r.get('hours',2)*3600<=ts<target:continue
   when=datetime.fromtimestamp(target,ZoneInfo('Asia/Ho_Chi_Minh')).strftime('%d/%m/%Y %H:%M')
   for e in enrolled:
    m=all_members.get(e['member_id'])
    if e['course_id']!=row['course_id'] or not m or m['disabled'] or m['role']!='student' or kind=='end' and (rid,m['id']) in submitted:continue
    for role in ['students','parents']:
     if not r.get(role):continue
     key=hashlib.sha256(json.dumps([rid,kind,anchor,m['id'],role]).encode()).hexdigest()
     if key in seen:continue
     parent=role=='parents';title=('Nhắc giờ mở đề: ' if kind=='start' else 'Nhắc hạn nộp: ')+d['title']
     body=('Kính gửi phụ huynh em ' if parent else 'Nhắc em ')+m['name']+' · Lớp '+c['name']+' · '+c['subject']+'\n'+d['title']+'\n'+('Mở đề lúc: ' if kind=='start' else 'Hạn nộp: ')+when+' (giờ Việt Nam).\n'+('Học sinh chưa nộp bài. Vui lòng hoàn thành trước hạn.' if kind=='end' else 'Vui lòng chuẩn bị và đăng nhập đúng giờ.')
     data=dict(title=title,body=body,memberId=m['id'],read=False,reminder=True,parentReminder=parent,assignmentId=rid)
     if not db.execute(select(records.c.id).where(records.c.id=='assignment_reminder_'+key)).first():db.execute(insert(records).values(id='assignment_reminder_'+key,course_id=row['course_id'],kind='message',author_id=row['author_id'],data=json.dumps(data,ensure_ascii=False),created_at=datetime.fromtimestamp(ts,timezone.utc).isoformat()))
     seen.add(key);sent+=1
  if len(seen)!=before:d['_reminderSent']=sorted(seen);db.execute(update(records).where(records.c.id==rid).values(data=json.dumps(d,ensure_ascii=False)))
 return sent
