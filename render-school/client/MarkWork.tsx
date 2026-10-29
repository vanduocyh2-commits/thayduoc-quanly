import React,{useState} from 'react';
import MathText from './MathText';
import {answerText,questionLabel} from './ExamQuestions';
import {submissionAttempts} from './gradebook.mjs';
import {WorkFiles} from './ExamTaking';
export default function MarkWork({submission,exam}:any){
 const attempts=submissionAttempts(submission.data,submission.created_at),[number,setNumber]=useState(submission.data.attemptCount||1),attempt=attempts.find((a:any)=>a.attemptCount===number)||attempts[0];
 const d=exam?.variants?.find((v:any)=>v.code===attempt.examCode)||exam;
 return <><label>Lần làm bài<select name="attemptCount" value={number} onChange={e=>setNumber(Number(e.target.value))}>{attempts.map((a:any)=><option key={a.attemptCount} value={a.attemptCount}>Lần {a.attemptCount} · {a.submittedAt?new Date(a.submittedAt).toLocaleString('vi-VN',{timeZone:'Asia/Ho_Chi_Minh'}):''} · {a.score===null?'Chờ chấm':a.score+'/10'}</option>)}</select></label><div key={number}>{attempt.summaryOnly&&<p className="notice">Lần làm cũ chỉ còn lưu điểm tổng kết. Các lần gần nhất và bài có điểm cao nhất giữ nội dung chi tiết.</p>}{attempt.examCode&&<p>Mã đề: <b>{attempt.examCode}</b></p>}<p className="body-text">{attempt.text}</p><WorkFiles files={attempt.attachments}/>{attempt.quizScore!==undefined&&<p>Điểm trắc nghiệm tự chấm: <b>{attempt.quizScore}</b>. Nhập tổng điểm sau khi chấm tự luận.</p>}{!attempt.summaryOnly&&d?.questions?.map((q:any,i:number)=><div className="question" key={i}><b>{questionLabel({...exam,...d},q,i)}.</b><MathText text={q.text}/><p>Học sinh trả lời: <MathText text={answerText(q,attempt.answers?.[i])} inline/></p><p>Đáp án: <MathText text={answerText(q,q.correct)} inline/></p></div>)}<label>Điểm / 10<input name="score" type="number" min="0" max="10" step="0.01" required defaultValue={attempt.score??''}/></label><label>Nhận xét<textarea name="feedback" defaultValue={attempt.feedback||''}/></label></div></>
}
