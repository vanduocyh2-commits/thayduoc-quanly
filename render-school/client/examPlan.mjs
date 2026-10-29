export const newId=()=>globalThis.crypto?.randomUUID?.()||Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);
export const LEVELS=['Nhận biết','Thông hiểu','Vận dụng','Vận dụng cao'];
export const TYPES={quiz:'Trắc nghiệm 4 lựa chọn',truefalse:'Đúng / Sai (4 ý)',short:'Trả lời ngắn',essay:'Tự luận'};
export const sum=a=>a.reduce((n,v)=>n+Number(v||0),0);
// Largest remainders keep the exact question count for every row.
export function allocate(count,ratios){
 if(!Number.isInteger(count)||count<0||count>100||ratios.length!==4||ratios.some(n=>!Number.isFinite(n)||n<0)||Math.abs(sum(ratios)-100)>.001)throw Error('Tỷ lệ mức độ phải đủ 100%; số câu là số nguyên từ 0 đến 100.');
 const raw=ratios.map(n=>count*n/100),out=raw.map(Math.floor);
 const order=raw.map((n,i)=>({i,f:n-out[i]})).sort((a,b)=>b.f-a.f||a.i-b.i);
 for(let n=count-sum(out),i=0;i<n;i++)out[order[i].i]++;
 return out;
}
export function makeQuestions(rows){
 if(rows.some(r=>!Object.hasOwn(TYPES,r.type)||!Array.isArray(r.counts)||r.counts.length!==4||r.counts.some(n=>!Number.isInteger(n)||n<0||n>100)||!Number.isFinite(Number(r.points))||Number(r.points)<=0))throw Error('Kiểm tra số câu nguyên và điểm từng hàng.');
 const count=sum(rows.map(r=>sum(r.counts)));
 if(!count||count>100)throw Error('Đề cần từ 1 đến 100 câu.');
 return rows.flatMap(r=>r.counts.flatMap((n,l)=>Array.from({length:n},()=>({id:newId(),rowId:r.id,type:r.type,text:'',topic:r.topic||'',level:LEVELS[l],points:Number(r.points),outcome:'',answers:['','','',''],correct:r.type==='truefalse'?[true,true,true,true]:r.type==='short'?'':0}))));
}
export function actualMatrix(qs){
 const topics=[...new Set(qs.map(q=>q.topic||'Chưa đặt chủ đề'))];
 return topics.map(topic=>({topic,levels:LEVELS.map(level=>{const a=qs.filter(q=>(q.topic||'Chưa đặt chủ đề')===topic&&q.level===level);return {count:a.length,points:sum(a.map(q=>q.points)),types:Object.keys(TYPES).map(type=>({type,count:a.filter(q=>q.type===type).length})).filter(x=>x.count)};})}));
}
export function shuffled(values,random=Math.random){
 const a=[...values];for(let i=a.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;
}
export function makeVariants(qs,count,shuffleQuestions,shuffleAnswers,random=Math.random){
 if(!Number.isInteger(count)||count<1||count>10)throw Error('Số mã đề từ 1 đến 10.');
 return Array.from({length:count},(_,v)=>{
  const ordered=Object.keys(TYPES).flatMap(type=>{const a=qs.filter(q=>q.type===type);return shuffleQuestions?shuffled(a,random):a});
  const questions=ordered.map(q=>{
   if(q.type!=='quiz'||!shuffleAnswers)return {...q};
   const indexes=shuffled([0,1,2,3],random);return {...q,answers:indexes.map(i=>q.answers[i]),correct:indexes.indexOf(q.correct)};
  });
  return {code:String(101+v),questions:questions.filter(q=>q.type!=='essay'),essays:questions.filter(q=>q.type==='essay')};
 });
}
export function parseExamImport(source){
 if(source.length>1024*1024)throw Error('Nội dung nhập tối đa 1 MB.');
 const fenced=source.match(/```(?:json)?\s*([\s\S]*?)```/i);
 let data;try{data=JSON.parse(fenced?fenced[1]:source)}catch{throw Error('Cần JSON theo mẫu đã sao chép; có thể đặt trong khối ```json của Markdown.');}
 const list=Array.isArray(data)?data:data.questions;
 if(!Array.isArray(list)||!list.length||list.length>100)throw Error('Cần danh sách questions gồm 1–100 câu.');
 return list.map((q,i)=>{
  const bad=()=>{throw Error(`Câu ${i+1} chưa đúng mẫu: kiểm tra dạng, điểm, mức độ, nội dung và đáp án.`)};
  if(!q||typeof q!=='object'||!Object.hasOwn(TYPES,q.type)||typeof q.text!=='string'||!q.text.trim()||q.text.length>2000||typeof q.topic!=='string'||!q.topic.trim()||q.topic.length>200||!LEVELS.includes(q.level)||typeof q.outcome!=='string'||!q.outcome.trim()||q.outcome.length>2000||!Number.isFinite(q.points)||q.points<=0||q.points>10)bad();
  if(['quiz','truefalse'].includes(q.type)&&(!Array.isArray(q.answers)||q.answers.length!==4||q.answers.some(a=>typeof a!=='string'||!a.trim()||a.length>1000)))bad();
  if(q.type==='quiz'&&(!Number.isInteger(q.correct)||q.correct<0||q.correct>3))bad();
  if(q.type==='truefalse'&&(!Array.isArray(q.correct)||q.correct.length!==4||q.correct.some(v=>typeof v!=='boolean')))bad();
  if(q.type==='short'&&(typeof q.correct!=='string'||!q.correct.trim()||q.correct.length>200))bad();
  return {id:newId(),rowId:q.type,type:q.type,text:q.text,topic:q.topic,level:q.level,outcome:q.outcome,points:q.points,answers:q.answers||['','','',''],correct:q.correct??0,ignoreCase:q.ignoreCase===true};
 });
}
