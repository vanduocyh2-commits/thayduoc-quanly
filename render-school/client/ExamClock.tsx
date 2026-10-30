import React,{useEffect,useState} from 'react';
import {remainingSeconds,clockText} from './examClock.mjs';
export default function ExamClock({assignmentId,csrf}:any){
 const [clock,setClock]=useState<any>(null),[error,setError]=useState(''),[seconds,setSeconds]=useState<number|null>(null),[retry,setRetry]=useState(0);
 useEffect(()=>{let active=true;const controller=new AbortController();let pending=false;
  async function sync(){if(pending)return;pending=true;try{const start=performance.now(),r=await fetch('/api/exams/'+encodeURIComponent(assignmentId)+'/clock',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:'{}',signal:controller.signal}),d=await r.json();if(!r.ok)throw Error(d.error||'Chưa lấy được giờ làm bài.');if(active){const value={...d,received:performance.now(),serverNow:d.serverNow+(performance.now()-start)/2};setClock(value);setSeconds(remainingSeconds(value.deadline,value.serverNow));setError('')}}catch(e:any){if(active&&e.name!=='AbortError')setError(e.message)}finally{pending=false}}
  sync();const refresh=()=>{if(document.visibilityState==='visible')sync()};document.addEventListener('visibilitychange',refresh);const timer=setInterval(sync,60000);
  return()=>{active=false;controller.abort();clearInterval(timer);document.removeEventListener('visibilitychange',refresh)};
 },[assignmentId,csrf,retry]);
 useEffect(()=>{if(!clock)return;const tick=()=>setSeconds(remainingSeconds(clock.deadline,clock.serverNow+performance.now()-clock.received));tick();const timer=setInterval(tick,250);return()=>clearInterval(timer)},[clock]);
 return <div className={'exam-clock '+(seconds!==null&&seconds<=300?'exam-clock-warning':'')}>
 <div className="exam-clock-label">{seconds===0?'Đã hết thời gian':'Thời gian còn lại'}</div><strong role="timer" aria-label={seconds===null?'Thời gian làm bài':clockText(seconds)}>{clock?seconds===null?'Không giới hạn':clockText(seconds):'Đang tải…'}</strong>
 {seconds===0&&<p role="status">Hãy bấm Nộp bài để gửi bài làm.</p>}{error&&<div role="status" className="exam-clock-error">{clock?'Đang mất kết nối đồng hồ. ':''}{error} <button type="button" className="secondary mini" onClick={()=>setRetry(n=>n+1)}>Thử lại</button></div>}
 </div>
}
