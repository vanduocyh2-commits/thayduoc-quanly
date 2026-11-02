import React,{useState} from 'react';

export default function QuestionClassificationFields({q,i,change,options=[]}:any){
 const [custom,setCustom]=useState(false);
 const choices=[...new Set([...(options||[]),q.topic].map((value:any)=>String(value||'').trim()).filter(Boolean))];
 const selected=String(q.topic||'');
 return <div className="exam-meta">
  <label>Chọn chủ đề / chương / bài
   <select required value={custom?'__custom__':selected} onChange={e=>{
    if(e.target.value==='__custom__'){setCustom(true);change(i,'topic','');return}
    setCustom(false);change(i,'topic',e.target.value);
   }}>
    <option value="">Chọn chủ đề, chương hoặc bài học</option>
    {choices.map((value:string)=><option key={value} value={value}>{value}</option>)}
    <option value="__custom__">＋ Nhập tên khác…</option>
   </select>
  </label>
  {custom&&<label>Tên chủ đề / chương / bài<input required maxLength={200} value={selected} onChange={e=>change(i,'topic',e.target.value)} placeholder="Ghi rõ tên chủ đề, chương hoặc bài"/></label>}
 </div>;
}