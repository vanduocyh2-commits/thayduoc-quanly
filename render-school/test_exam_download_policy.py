import io,json
from test_school import app,client,action,state,token
from test_school_workflows import school
from test_exam_code_policy import payload

def create_pdf(t,cid,variants=False,**extra):
 p=payload(cid,**extra)
 if not variants:p['data'].pop('variants')
 else:p['data']['source']='uploaded'
 files={'payload':json.dumps(p)}
 for code in (['101','102'] if variants else ['']):files['file_'+code if code else 'file']=(io.BytesIO(b'%PDF-1.4\nsynthetic\n%%EOF'),'exam.pdf')
 r=t.post('/api/exams',data=files,headers={'Origin':'http://localhost','X-CSRF-Token':token(t)})
 assert r.status_code==200,r.json
 return next(r for r in state(t)['records'] if r['kind']=='assignment')['id']

def test_teacher_controls_download_and_preview_remains_available(school,app):
 admin,cs,ids,cid,_=school;t=cs['teacher'];s=cs['stu1'];rid=create_pdf(t,cid)
 url=next(r['data']['file']['url'] for r in state(s)['records'] if r['id']==rid)
 assert s.get(url).status_code==200
 settings=dict(action='assignmentSettings',id=rid,allowDownload=False)
 for actor in [s,cs['other']]:assert action(actor,settings).status_code==403
 assert action(t,{**settings,'allowDownload':'false'}).status_code==400
 assert action(t,settings).status_code==200
 assert next(r['data']['file'] for r in state(s)['records'] if r['id']==rid)['downloadAllowed'] is False
 assert s.get(url).status_code==403
 assert s.get(url+'?preview=0').status_code==403
 preview=s.get(url+'?preview=1');assert preview.status_code==200 and 'inline' in preview.headers['Content-Disposition'] and preview.headers['Cache-Control']=='no-store'
 assert t.get(url).status_code==200
 assert app.test_client().get(url+'?preview=1').status_code==401
 assert action(t,{**settings,'allowDownload':True}).status_code==200
 assert s.get(url).status_code==200

def test_variant_download_cannot_bypass_assigned_code_and_bank_copy_is_independent(school):
 admin,cs,ids,cid,_=school;t=cs['teacher'];s=cs['stu1'];rid=create_pdf(t,cid,True,allowDownload=False,codePolicy='fixed',fixedExamCode='102')
 d=next(r['data'] for r in state(s)['records'] if r['id']==rid);assert d['file']['downloadAllowed'] is False
 url=d['file']['url'];assert s.get(url).status_code==403 and s.get(url+'?preview=1').status_code==200
 assert s.get('/api/exams/'+rid+'/files/101?preview=1').status_code==403
 assert t.get('/api/exams/'+rid+'/files/101').status_code==200
 assert action(t,{'action':'assignBankExam','id':rid,'courseId':cid,'allowDownload':True}).status_code==200
 copied=next(r for r in state(s)['records'] if r['data'].get('bankSourceId')==rid)
 assert s.get(copied['data']['file']['url']).status_code==200
 assert next(r['data'] for r in state(t)['records'] if r['id']==rid)['allowDownload'] is False
 assert action(t,payload(cid,allowDownload='false')).status_code==400
