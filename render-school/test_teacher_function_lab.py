from test_school import app,client
from test_school_workflows import school

def test_graph_tool_requires_staff_session_and_is_isolated_from_portal(school,app):
 admin,cs,ids,cid,_=school;url='/api/teacher-tools/function-lab'
 assert app.test_client().get(url).status_code==401
 assert cs['stu1'].get(url).status_code==403
 for actor in [admin,cs['teacher']]:
  r=actor.get(url);assert r.status_code==200 and r.mimetype=='text/html'
  assert r.headers['X-Frame-Options']=='SAMEORIGIN' and r.headers['Cache-Control']=='no-store'
  policy=r.headers['Content-Security-Policy'];assert 'sandbox allow-scripts allow-downloads' in policy and 'allow-same-origin' not in policy and "connect-src 'none'" in policy and 'unsafe-eval' not in policy
  assert 'Bảng biến thiên'.encode() in r.data and b'saveCanvasImage' in r.data and b'new Function' not in r.data
