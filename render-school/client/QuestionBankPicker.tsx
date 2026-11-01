import React,{useMemo,useState} from 'react';
import MathText from './MathText';

const TYPES:any={quiz:'Trắc nghiệm 4 lựa chọn',truefalse:'Đúng / Sai',short:'Trả lời ngắn',essay:'Tự luận'};
const LEVELS=['Nhận biết','Thông hiểu','Vận dụng','Vận dụng cao'];
const clean=(value:any)=>String(value??'').trim();

export default function QuestionBankPicker({entries=[],course,grade,currentUser,onAdd}:any){
 const [filters,setFilters]=useState<any>(()=>({grade:String(grade||course?.grade||''),subject:clean(course?.subject),curriculum:'',textbook:'',chapter:'',lesson:'',level:'',type:'',search:''}));
 const [selected,setSelected]=useState<string[]>([]);
 const all=useMemo(()=>entries.map((row:any)=>{
  const q={...(row?.data||row)};
  const id=String(row?.id||q.bankId||q.id||'');
  return {...q,data:q,id,bankId:id,ownerId:row?.author_id||q.ownerId||'',author_id:row?.author_id||q.author_id||'',courseLabel:row?.course_label||'',authorName:row?.author_name||''};
 }).filter((q:any)=>q.id&&clean(q.text)),[entries]);
 const values=(key:string)=>[...new Set(all.map((q:any)=>clean(q[key])).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'vi',{numeric:true}));
 const filtered=all.filter((q:any)=>!filters.grade||String(q.grade||'')===filters.grade)
  .filter((q:any)=>!filters.subject||clean(q.subject)===filters.subject)
  .filter((q:any)=>!filters.curriculum||clean(q.curriculum)===filters.curriculum)
  .filter((q:any)=>!filters.textbook||clean(q.textbook)===filters.textbook)
  .filter((q:any)=>!filters.chapter||clean(q.chapter)===filters.chapter)
  .filter((q:any)=>!filters.lesson||clean(q.lesson)===filters.lesson)
  .filter((q:any)=>!filters.level||clean(q.level)===filters.level)
  .filter((q:any)=>!filters.type||clean(q.type)===filters.type)
  .filter((q:any)=>!filters.search||[q.text,q.topic,q.outcome,q.subject,q.curriculum,q.textbook,q.chapter,q.lesson].join(' ').toLocaleLowerCase('vi').includes(filters.search.toLocaleLowerCase('vi')))
  .slice(0,100);
 const set=(key:string,value:string)=>setFilters((old:any)=>({...old,[key]:value}));
 const select=(key:string,label:string,options:string[])=><label key={key}>{label}<select value={filters[key]} onChange={e=>set(key,e.target.value)}><option value="">Tất cả</option>{options.map(v=><option key={v} value={v}>{v}</option>)}</select></label>;
 const typeSelect=<label>Dạng câu hỏi<select value={filters.type} onChange={e=>set('type',e.target.value)}><option value="">Tất cả</option>{Object.entries(TYPES).map(([key,label])=><option key={key} value={key}>{label as string}</option>)}</select></label>;
 const add=(items:any[])=>{
  const picked=items.filter(Boolean);
  if(!picked.length)return;
  onAdd?.(picked);
  setSelected([]);
 };
 const clear=()=>{setFilters({grade:'',subject:'',curriculum:'',textbook:'',chapter:'',lesson:'',level:'',type:'',search:''});setSelected([])};
 return <section className="exam-section question-bank-picker">
  <details>
   <summary><b>Ngân hàng câu hỏi</b> · {all.length} câu đã lưu · Chọn câu để đưa vào đề thường hoặc đề ma trận</summary>
   <div className="exam-meta">
    {select('grade','Khối',values('grade'))}
    {select('subject','Môn học',values('subject'))}
    {select('curriculum','Chương trình',values('curriculum'))}
    {select('textbook','Bộ sách',values('textbook'))}
    {select('chapter','Chương',values('chapter'))}
    {select('lesson','Bài học',values('lesson'))}
    {select('level','Mức độ',LEVELS)}
    {typeSelect}
    <label>Tìm câu hỏi<input value={filters.search} onChange={e=>set('search',e.target.value)} placeholder="Tìm nội dung, chủ đề, yêu cầu cần đạt…"/></label>
   </div>
   <div className="toolbar">
    <button type="button" className="secondary mini" onClick={clear}>Xóa bộ lọc</button>
    <span className="muted">{filtered.length} câu phù hợp{all.length>100?' · Đang hiển thị tối đa 100 câu':''}</span>
    <button type="button" disabled={!selected.length} onClick={()=>add(filtered.filter((q:any)=>selected.includes(q.id)))}>＋ Đưa {selected.length} câu đã chọn vào đề</button>
   </div>
   <div className="question-bank-picker-list">
    {filtered.map((q:any)=><article className="card question-bank-picker-row" key={q.id}>
     <label className="checkline"><input type="checkbox" checked={selected.includes(q.id)} onChange={e=>setSelected(old=>e.target.checked?[...new Set([...old,q.id])]:old.filter(id=>id!==q.id))}/><span><b>{TYPES[q.type]||q.type} · {q.level||'Chưa phân mức'} · {Number(q.points)||0} điểm</b><small>{[q.subject,'Khối '+(q.grade||''),q.curriculum,q.textbook,q.chapter,q.lesson].filter(Boolean).join(' · ')}</small></span></label>
     <div className="question-bank-picker-text"><MathText text={q.text}/></div>
     <small className="muted">{q.courseLabel}{q.authorName?' · '+q.authorName:''}{q.topic?' · '+q.topic:''}</small>
     <button type="button" className="secondary mini" onClick={()=>add([q])}>＋ Đưa câu này vào đề</button>
    </article>)}
    {!filtered.length&&<p className="empty">Không có câu hỏi phù hợp. Thầy có thể phân loại câu ở bên dưới rồi lưu đề để bổ sung vào ngân hàng.</p>}
   </div>
  </details>
 </section>;
}
