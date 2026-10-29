const numeric = value => typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 10;
const number = (value, fallback=1) => Number.isInteger(value) && value > 0 ? value : fallback;
export function submissionAttempts(data, createdAt='') {
 const rows=new Map();
 const sources=[{...data,submittedAt:createdAt},...(data.history||[]).slice().reverse(),...(data.bestAttempt?[data.bestAttempt]:[]),...(data.attemptScores||[]).map(row=>({...row,summaryOnly:true}))];
 for(const source of sources){const n=number(source.attemptCount);if(!rows.has(n))rows.set(n,{...source,attemptCount:n,score:numeric(source.score)?source.score:null});}
 return [...rows.values()].sort((a,b)=>b.attemptCount-a.attemptCount);
}
export function bestSubmissionScore(data, createdAt='') {
 const values=submissionAttempts(data,createdAt).map(row=>row.score).filter(numeric);
 return values.length?Math.max(...values):null;
}
export function dayKey(value){
 if(typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value))return value;
 const date=new Date(value);if(!value||!Number.isFinite(date.getTime()))return '';
 const parts=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(date).map(p=>[p.type,p.value]));
 return `${parts.year}-${parts.month}-${parts.day}`;
}
export const dateLabel = day => day?day.split('-').reverse().join('/'):'Chưa có ngày';
export const formatScore = score => numeric(score)?score.toLocaleString('vi-VN',{maximumFractionDigits:2}):'—';
export function examClosed(data, now=Date.now()){return !!data.closedAt||!!data.due&&Number.isFinite(Date.parse(data.due))&&now>=Date.parse(data.due);}
export function buildCourseGradebook(state, course, now=Date.now()){
 const ids=new Set(state.enrollments.filter(e=>e.course_id===course.id).map(e=>e.member_id));
 const students=state.members.filter(m=>m.role==='student'&&ids.has(m.id)).slice().sort((a,b)=>a.name.localeCompare(b.name,'vi')||a.id.localeCompare(b.id));
 const records=state.records.filter(r=>r.course_id===course.id),columns=[],manual=new Map();
 for(const record of records){const d=record.data;
  if(record.kind==='assignment')columns.push({id:'exam:'+record.id,assignmentId:record.id,title:d.title,day:dayKey(d.opensAt||record.created_at),closed:examClosed(d,now),kind:'exam',createdAt:record.created_at});
  if(record.kind==='grade'){
   const day=dayKey(d.date||record.created_at),key=JSON.stringify([d.title.trim().normalize('NFC').toLocaleLowerCase('vi'),day]);
   if(!manual.has(key)){const column={id:'manual:'+key,title:d.title,day,kind:'manual',createdAt:record.created_at,records:[]};manual.set(key,column);columns.push(column);}
   manual.get(key).records.push(record);
  }
 }
 columns.sort((a,b)=>a.day.localeCompare(b.day)||a.createdAt.localeCompare(b.createdAt)||a.id.localeCompare(b.id));
 const submissions=new Map(state.submissions.map(sub=>[JSON.stringify([sub.assignment_id,sub.member_id]),sub]));
 const rows=students.map(student=>{const cells=columns.map(column=>{
  if(column.kind==='exam'){const sub=submissions.get(JSON.stringify([column.assignmentId,student.id]));return {columnId:column.id,score:sub?bestSubmissionScore(sub.data,sub.created_at):null,status:sub?(sub.data.scoreHidden?'Chưa công bố':'Chờ chấm'):'Chưa thi',submissionId:sub?.id,attemptCount:sub?.data.bestAttemptCount};}
  const grade=column.records.filter(r=>r.data.memberId===student.id).sort((a,b)=>b.created_at.localeCompare(a.created_at)||b.id.localeCompare(a.id))[0];
  return {columnId:column.id,score:numeric(grade?.data.score)?grade.data.score:null,status:'—'};
 });const scores=cells.map(c=>c.score).filter(numeric);return {student,cells,count:scores.length,average:scores.length?Math.round(scores.reduce((a,b)=>a+b,0)/scores.length*100)/100:null};});
 return {course,columns,rows};
}
export function gradebookCsv(books){
 const cell=value=>'"'+String(value??'').replace(/^\s*[=+@-]/,"'$&").replace(/"/g,'""')+'"';
 const rows=[];for(const book of books){rows.push([book.course.name,book.course.subject]);rows.push(['STT','Học sinh',...book.columns.map(c=>`${dateLabel(c.day)} · ${c.title}`),'Điểm trung bình','Số cột có điểm']);book.rows.forEach((row,i)=>rows.push([i+1,row.student.name,...row.cells.map(c=>c.score??''),row.average??'',row.count]));rows.push([]);}
 return '\ufeff'+rows.map(row=>row.map(cell).join(',')).join('\r\n');
}
