import React,{useState} from 'react';
import {knttMathBookForValue,knttMathBooksForGrade} from './questionBankCatalog';

const clean=(value:any)=>String(value??'').trim();
const unique=(values:any[])=>[...new Set(values.map(clean).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'vi',{numeric:true}));

export default function QuestionClassificationFields({q,i,grade,subject,change,questionBank=[]}:any){
 const [custom,setCustom]=useState<Record<string,boolean>>({});
 const selectedGrade=String(q.grade||grade||'10');
 const selectedSubject=String(q.subject||subject||'');
 const isMath=/toán/i.test(selectedSubject);
 const useKntt=isMath&&['10','11','12'].includes(selectedGrade);
 const books=knttMathBooksForGrade(selectedGrade);
 const book=knttMathBookForValue(selectedGrade,String(q.textbook||''));
 const chapters=book?.chapters||[];
 const chapter=chapters.find(row=>row.title===q.chapter);
 const lessons=chapter?.lessons||[];
 const bank=(questionBank||[]).map((row:any)=>row?.data||row).filter((row:any)=>row&&
   (!selectedSubject||clean(row.subject)===clean(selectedSubject))&&
   (!selectedGrade||String(row.grade||'')===selectedGrade));
 const scoped=bank.filter((row:any)=>!q.curriculum||!row.curriculum||clean(row.curriculum)===clean(q.curriculum));
 const byBook=scoped.filter((row:any)=>!q.textbook||!row.textbook||clean(row.textbook)===clean(q.textbook));
 const byChapter=byBook.filter((row:any)=>!q.chapter||!row.chapter||clean(row.chapter)===clean(q.chapter));
 const curricula=unique([...scoped.map((row:any)=>row.curriculum),'GDPT 2018',q.curriculum]);
 const textbooks=useKntt?books.map((row:any)=>row.textbook):unique([...scoped.map((row:any)=>row.textbook),q.textbook]);
 const topicOptions=unique([...(useKntt?chapters.map((row:any)=>row.title):[]),...scoped.map((row:any)=>row.topic),q.topic]);
 const chapterOptions=useKntt?chapters.map((row:any)=>row.title):unique([...byBook.map((row:any)=>row.chapter),q.chapter]);
 const lessonOptions=useKntt?lessons.map((row:any)=>row.title):unique([...byChapter.map((row:any)=>row.lesson),q.lesson]);

 function pick(label:string,key:string,options:string[],onPick?:(value:string)=>void,disabled=false){
  const value=clean(q[key]),isCustom=!!custom[key]||!!(value&&!options.includes(value));
  const setValue=(next:string)=>{if(onPick)onPick(next);else change(i,key,next)};
  return <React.Fragment key={key}>
   <label>{label}<select required value={isCustom?'__custom__':value} disabled={disabled} onChange={e=>{
    const next=e.target.value;
    if(next==='__custom__'){setCustom(old=>({...old,[key]:true}));return}
    setCustom(old=>({...old,[key]:false}));setValue(next);
   }}><option value="">Chọn {label.toLocaleLowerCase('vi')}</option>{options.map(option=><option key={option} value={option}>{option}</option>)}<option value="__custom__">＋ Nhập {label.toLocaleLowerCase('vi')} khác…</option></select></label>
   {isCustom&&<label>{label} mới<input required maxLength={200} value={value} onChange={e=>setValue(e.target.value)} placeholder={'Nhập '+label.toLocaleLowerCase('vi')}/></label>}
  </React.Fragment>;
 }
 const setGrade=(value:string)=>change(i,{grade:value,textbook:'',chapter:'',chapterOrder:1,lesson:'',lessonOrder:1});
 const setBook=(value:string)=>change(i,{textbook:value,chapter:'',chapterOrder:1,lesson:'',lessonOrder:1});
 const setChapter=(value:string)=>{
  const selected=chapters.find((row:any)=>row.title===value);
  change(i,{chapter:value,chapterOrder:selected?.order||1,lesson:'',lessonOrder:1,...(!q.topic&&selected?{topic:selected.title}:{})});
 };
 const setLesson=(value:string)=>{
  const selected=lessons.find((row:any)=>row.title===value);
  change(i,{lesson:value,lessonOrder:selected?.order||1});
 };
 return <div className="exam-meta">
  <label>Môn học<input required maxLength={120} value={selectedSubject} readOnly/></label>
  <label>Khối<select required value={selectedGrade} onChange={e=>setGrade(e.target.value)}>{unique(['10','11','12',selectedGrade]).sort((a,b)=>Number(a)-Number(b)).map(value=><option key={value} value={value}>Lớp {value}</option>)}</select></label>
  {pick('Chủ đề / mạch kiến thức','topic',topicOptions)}
  {pick('Chương trình','curriculum',curricula)}
  {pick('Bộ sách / tài liệu','textbook',textbooks,setBook)}
  {pick('Chương','chapter',chapterOptions,setChapter)}
  {useKntt?<label>Thứ tự chương<input type="number" min="1" max="999" readOnly value={chapter?.order||q.chapterOrder||1}/></label>:<label>Thứ tự chương<input type="number" min="1" max="999" value={q.chapterOrder||1} onChange={e=>change(i,'chapterOrder',Number(e.target.value))}/></label>}
  {pick('Bài học','lesson',lessonOptions,setLesson,!q.chapter)}
  {useKntt?<label>Thứ tự bài<input type="number" min="1" max="999" readOnly value={lessons.find((row:any)=>row.title===q.lesson)?.order||q.lessonOrder||1}/></label>:<label>Thứ tự bài<input type="number" min="1" max="999" value={q.lessonOrder||1} onChange={e=>change(i,'lessonOrder',Number(e.target.value))}/></label>}
 </div>;
}
