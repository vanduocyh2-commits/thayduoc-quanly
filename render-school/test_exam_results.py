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
