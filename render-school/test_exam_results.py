from exam_results import with_best_result,grade_attempt

def test_best_survives_history_limit_and_later_pending_attempt():
 d={'score':9,'attemptCount':1,'text':'best'};with_best_result(d,'t1')
 for number in range(2,27):
  old=d
  d={'attemptCount':number,'score':None if number==26 else 3,'history':(old.get('history',[])+[{k:v for k,v in old.items() if k not in ['history','bestAttempt','bestScore','bestAttemptCount','bestSubmittedAt','attemptScores']}])[-20:],'bestAttempt':old['bestAttempt'],'attemptScores':old['attemptScores']}
  with_best_result(d,'t'+str(number))
 assert len(d['history'])==20
 assert len(d['attemptScores'])==26
 assert d['bestScore']==9 and d['bestAttempt']['text']=='best'
 d=grade_attempt(d,'t26',1,2,'corrected','now','t')
 assert d['bestScore']==3
 d=grade_attempt(d,'t26',26,10,'new best','now','t')
 assert d['bestScore']==10 and d['bestAttemptCount']==26

def test_zero_counts_and_invalid_scores_do_not():
 assert with_best_result({'score':0},'now')['bestScore']==0
 for score in [True,float('nan'),float('inf'),-1,11,'10',None]:assert with_best_result({'score':score},'now')['bestScore'] is None

def test_attempt_timing_survives_best_result_ledger_and_regrading():
 from exam_results import attach_attempt_times
 d={'score':8,'attemptCount':1,'submittedAt':'2026-10-31T01:10:00Z'}
 attach_attempt_times(d,d['submittedAt'],{1:1793408400}) # 01:00 UTC
 assert d['durationSeconds']==600
 with_best_result(d,d['submittedAt']);assert d['bestAttempt']['durationSeconds']==600
 second={'score':3,'attemptCount':2,'submittedAt':'2026-10-31T02:20:00Z','history':[d],'bestAttempt':d['bestAttempt'],'attemptScores':d['attemptScores']}
 attach_attempt_times(second,second['submittedAt'],{1:1793408400,2:1793412000});with_best_result(second,second['submittedAt'])
 assert second['durationSeconds']==1200 and second['bestAttempt']['durationSeconds']==600
 assert second['attemptScores'][0]['durationSeconds']==600
 grade_attempt(second,second['submittedAt'],2,9,'','now','teacher');assert second['bestAttemptCount']==2 and second['bestAttempt']['durationSeconds']==1200

def test_unknown_or_invalid_start_does_not_invent_exam_duration():
 from exam_results import attach_attempt_times
 d={'score':7,'attemptCount':1};attach_attempt_times(d,'2026-10-31T01:00:00Z',{});assert 'startedAt' not in d and 'durationSeconds' not in d
 d={'score':7,'attemptCount':1,'startedAt':'bad'};attach_attempt_times(d,'2026-10-31T01:00:00Z',{});assert d['durationSeconds'] is None
