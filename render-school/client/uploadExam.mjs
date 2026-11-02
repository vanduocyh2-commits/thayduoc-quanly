const labels={quiz:'Trắc nghiệm',truefalse:'Đúng / Sai',short:'Trả lời ngắn',essay:'Tự luận'};
export const defaultUploadStructure=()=>[{type:'quiz',count:12,points:.25},{type:'truefalse',count:4,points:1},{type:'short',count:6,points:.5},{type:'essay',count:0,points:1}];
export function uploadedQuestions(structure,keys,topic='Nội dung đề đính kèm'){
 if(structure.some(r=>!Number.isInteger(r.count)||r.count<0||r.count>100||!Number.isFinite(r.points)||r.points<=0)||structure.reduce((n,r)=>n+r.count,0)>100)throw Error('Số câu phải nguyên, tối đa 100 câu; điểm/câu phải lớn hơn 0.');
 if(Math.abs(structure.reduce((n,r)=>n+r.count*r.points,0)-10)>.001)throw Error('Cấu trúc đề phải đủ 10 điểm để tự chấm.');
 const qs=[];for(const row of structure){let entries=[];
 if(row.type==='quiz')entries=String(keys.quiz||'').toUpperCase().split(/[\s,;]+/).filter(Boolean);
 if(row.type==='truefalse')entries=String(keys.truefalse||'').trim().split(/\n/).filter(s=>s.trim()).map(s=>s.trim().toUpperCase().split(/[\s,;]+/).filter(Boolean).map(v=>['Đ','D','ĐÚNG','TRUE','1'].includes(v)?true:['S','SAI','FALSE','0'].includes(v)?false:null));
 if(row.type==='short')entries=String(keys.short||'').trim().split(/\n/).filter(s=>s.trim());
 if(row.type!=='essay'&&entries.length!==row.count)throw Error(`${labels[row.type]}: cần ${row.count} đáp án, đã nhập ${entries.length}.`);
 for(let i=0;i<row.count;i++){const q={type:row.type,text:`${labels[row.type]} câu ${i+1}: xem nội dung trong tệp đề đính kèm.`,topic,level:'Nhận biết',outcome:'Làm bài theo nội dung đề đính kèm',points:row.points};
 if(row.type==='quiz'){if(!/^[ABCD]$/.test(entries[i]))throw Error('Trắc nghiệm dùng đáp án A, B, C hoặc D.');q.answers=['A','B','C','D'];q.correct='ABCD'.indexOf(entries[i]);}
 if(row.type==='truefalse'){if(entries[i].length!==4||entries[i].some(v=>v===null))throw Error('Mỗi câu đúng/sai cần 4 ý Đ hoặc S.');q.answers=['Ý a','Ý b','Ý c','Ý d'];q.correct=entries[i];}
 if(row.type==='short'){q.correct=entries[i].trim();if(q.correct.length>200)throw Error('Đáp án ngắn tối đa 200 ký tự.');}
 qs.push(q);}}
 return {questions:qs.filter(q=>q.type!=='essay'),essays:qs.filter(q=>q.type==='essay')};
}
export function keysFromRows(rows){const keys={};for(const row of rows){const code=String(row.code),type=row.type;if(!/^\d{3,4}$/.test(code)||!['quiz','truefalse','short'].includes(type)||!Number.isInteger(Number(row.number))||Number(row.number)<1||Number(row.number)>100)throw Error('Đáp án cần mã đề 3–4 số, dạng quiz/truefalse/short và số câu 1–100.');keys[code]??={quiz:[],truefalse:[],short:[]};if(keys[code][type][Number(row.number)-1]!==undefined)throw Error('Trùng đáp án cùng mã đề, dạng và số câu.');keys[code][type][Number(row.number)-1]=String(row.answer??'');}
 const result={};for(const [code,k] of Object.entries(keys)){for(const values of Object.values(k))for(let i=0;i<values.length;i++)if(values[i]===undefined)throw Error('Số thứ tự câu trong mỗi dạng phải liên tục, bắt đầu từ 1.');result[code]={quiz:k.quiz.join(' '),truefalse:k.truefalse.join('\n'),short:k.short.join('\n')};}return result;
}

export function structureFromKeys(structure, keys){
 const counts=Object.values(keys).map(k=>({quiz:k.quiz.trim()?k.quiz.trim().split(/\s+/).length:0,truefalse:k.truefalse.trim()?k.truefalse.trim().split('\n').length:0,short:k.short.trim()?k.short.trim().split('\n').length:0}));
 if(!counts.length)throw Error('File chưa có đáp án.');
 if(counts.some(c=>Object.keys(c).some(type=>c[type]!==counts[0][type])))throw Error('Các mã đề cần có cùng số câu trong từng dạng.');
 return structure.map(row=>row.type==='essay'?row:{...row,count:counts[0][row.type]});
}
