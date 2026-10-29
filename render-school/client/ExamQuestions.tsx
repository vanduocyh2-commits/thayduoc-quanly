import React from 'react';
import MathText from './MathText';
export function readExamAnswer(f:FormData,q:any,i:number){
 if(q.type==='truefalse')return [0,1,2,3].map(j=>f.get(`q${i}_${j}`)==='true');
 if(q.type==='short')return String(f.get('q'+i)||'').trim();
 return f.get('q'+i)===null?null:Number(f.get('q'+i));
}
export function answerText(q:any,answer:any){
 if(q.type==='truefalse')return Array.isArray(answer)?answer.map((v,j)=>`${'abcd'[j]}. ${v?'Đúng':'Sai'}`).join('; '):'Chưa trả lời';
 if(q.type==='short')return answer||'Chưa trả lời';
 return q.answers?.[answer]||'Chưa trả lời';
}
export default function ExamQuestions({data,preview=false}:any){return <>
{data.minutes&&<p className="muted">Thời lượng đề: {data.minutes} phút · Khối {data.grade} · {data.subject}</p>}
{data.questions?.some((q:any)=>q.type==='truefalse')&&<p className="note">Đúng / Sai: {data.tfScoring==='equal'?'mỗi ý đúng được 25% điểm câu.':'đúng 1/2/3/4 ý được 10% / 25% / 50% / 100% điểm câu.'}</p>}
{data.questions?.map((q:any,i:number)=><fieldset key={i} className="question"><legend>Câu {i+1}. {q.points!==undefined&&`(${q.points} điểm)`}</legend><MathText text={q.text}/>
{q.type==='short'?<label>Câu trả lời<input type="text" name={'q'+i} required={!preview} maxLength={200}/></label>:q.type==='truefalse'?q.answers.map((a:string,j:number)=><div key={j}><div className="exam-answer-line"><b>{'abcd'[j]}.</b><MathText text={a}/></div><label><input type="radio" name={`q${i}_${j}`} value="true" required={!preview}/>Đúng</label><label><input type="radio" name={`q${i}_${j}`} value="false" required={!preview}/>Sai</label></div>):q.answers.map((a:string,j:number)=><label key={j}><input type="radio" name={'q'+i} value={j} required={!preview}/><b>{'ABCD'[j]}.</b><MathText text={a} inline/></label>)}
</fieldset>)}
{data.type!=='quiz'&&<>{data.essays?.map((q:any,i:number)=><div className="question" key={i}><b>Câu {(data.questions?.length||0)+i+1} · Tự luận. ({q.points} điểm)</b><MathText text={q.text}/></div>)}<label>Bài làm tự luận<textarea name="text" required={!preview} rows={10} maxLength={30000} placeholder="Ghi rõ số câu trước mỗi phần bài làm…"/></label></>}
</>}
