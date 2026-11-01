import React from 'react';
import {knttMathBookForValue,knttMathBooksForGrade} from './questionBankCatalog';

export default function QuestionClassificationFields({q,i,grade,subject,change}:any){
 const isMath=/toán/i.test(String(q.subject||subject||''));
 const selectedGrade=String(q.grade||grade||'10');
 const useKntt=isMath&&['10','11','12'].includes(selectedGrade);
 const books=knttMathBooksForGrade(selectedGrade);
 const book=knttMathBookForValue(selectedGrade,String(q.textbook||''));
 const chapters=book?.chapters||[];
 const chapter=chapters.find(row=>row.title===q.chapter);
 const lessons=chapter?.lessons||[];
 const manual=()=> <>
  <label>Khối<input required type="number" min="1" max="12" value={q.grade||grade} onChange={e=>change(i,{grade:e.target.value,textbook:'',chapter:'',chapterOrder:1,lesson:'',lessonOrder:1})}/></label>
  <label>Bộ sách<input maxLength={160} value={q.textbook||''} onChange={e=>change(i,{textbook:e.target.value,chapter:'',chapterOrder:1,lesson:'',lessonOrder:1})} placeholder="Ví dụ: Kết nối tri thức"/></label>
  <label>Chương<input required maxLength={160} value={q.chapter||''} onChange={e=>change(i,'chapter',e.target.value)} placeholder="Tên chương"/></label>
  <label>Thứ tự chương<input type="number" min="1" max="999" value={q.chapterOrder||1} onChange={e=>change(i,'chapterOrder',Number(e.target.value))}/></label>
  <label>Bài học<input required maxLength={160} value={q.lesson||''} onChange={e=>change(i,'lesson',e.target.value)} placeholder="Tên bài"/></label>
  <label>Thứ tự bài<input type="number" min="1" max="999" value={q.lessonOrder||1} onChange={e=>change(i,'lessonOrder',Number(e.target.value))}/></label>
 </>;
 return <div className="exam-meta">
  <label>Môn học<input required maxLength={120} value={q.subject||subject||''} onChange={e=>change(i,'subject',e.target.value)}/></label>
  {useKntt?<>
   <label>Khối<select required value={selectedGrade} onChange={e=>change(i,'grade',e.target.value)}>{['10','11','12'].map(value=><option key={value} value={value}>Lớp {value}</option>)}</select></label>
   <label>Chương trình<input required maxLength={160} value={q.curriculum||'GDPT 2018'} onChange={e=>change(i,'curriculum',e.target.value)}/></label>
   <label>Bộ sách / tập<select required value={book?q.textbook:''} onChange={e=>change(i,'textbook',e.target.value)}><option value="">Chọn Toán {selectedGrade} — Tập 1 hoặc Tập 2</option>{books.map(row=><option key={row.id} value={row.textbook}>{row.label}</option>)}</select></label>
   <label>Chương<select required disabled={!book} value={chapter?q.chapter:''} onChange={e=>{const selected=chapters.find(row=>row.title===e.target.value);change(i,'chapter',e.target.value);change(i,'chapterOrder',selected?.order||1);change(i,'lesson','');change(i,'lessonOrder',1)}}><option value="">{book?'Chọn chương':'Chọn tập trước'}</option>{chapters.map(row=><option key={row.id} value={row.title}>Chương {row.order}. {row.title}</option>)}</select></label>
   <label>Thứ tự chương<input type="number" min="1" max="999" readOnly value={chapter?.order||q.chapterOrder||1}/></label>
   <label>Bài học<select required disabled={!chapter} value={lessons.some(row=>row.title===q.lesson)?q.lesson:''} onChange={e=>{const selected=lessons.find(row=>row.title===e.target.value);change(i,'lesson',e.target.value);change(i,'lessonOrder',selected?.order||1)}}><option value="">{chapter?'Chọn bài học':'Chọn chương trước'}</option>{lessons.map(row=><option key={row.id} value={row.title}>{row.title}</option>)}</select></label>
   <label>Thứ tự bài<input type="number" min="1" max="999" readOnly value={lessons.find(row=>row.title===q.lesson)?.order||q.lessonOrder||1}/></label>
  </>:<>
   <label>Khối<input required type="number" min="1" max="12" value={q.grade||grade} onChange={e=>change(i,'grade',e.target.value)}/></label>
   <label>Chương trình<input required maxLength={160} value={q.curriculum||'GDPT 2018'} onChange={e=>change(i,'curriculum',e.target.value)}/></label>
   {manual()}
  </>}
 </div>;
}