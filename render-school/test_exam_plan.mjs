import {test} from 'node:test';import assert from 'node:assert/strict';
import {allocate,makeVariants,parseExamImport,makeQuestions,syncQuestionsToMatrix} from './client/examPlan.mjs';
test('allocation preserves every question count and rejects invalid ratios',()=>{for(let n=0;n<=100;n++){const a=allocate(n,[40,30,20,10]);assert.equal(a.reduce((x,y)=>x+y,0),n);assert.ok(a.every(Number.isInteger))}assert.deepEqual(allocate(2,[40,30,20,10]),[1,1,0,0]);assert.throws(()=>allocate(12,[40,30,20,0]));});
test('shuffling preserves the correct answer and never changes true/false meaning',()=>{const original=[{type:'quiz',answers:['a','b','c','d'],correct:1},{type:'truefalse',answers:['a','b','c','d'],correct:[true,false,true,false]},{type:'short',correct:'2'},{type:'essay',text:'Explain'}];const variants=makeVariants(original,10,true,true);assert.equal(new Set(variants.map(v=>v.code)).size,10);for(const v of variants){assert.equal(v.questions.find(q=>q.type==='quiz').answers[v.questions.find(q=>q.type==='quiz').correct],'b');assert.deepEqual(v.questions.find(q=>q.type==='truefalse'),original[1]);assert.equal(v.essays.length,1)}assert.deepEqual(original[0].answers,['a','b','c','d']);});
test('AI import validates question types and answer shapes before replacement',()=>{const q={type:'quiz',text:'$x^2$',points:10,level:'Nhận biết',topic:'Số',outcome:'Nhận biết',answers:['1','2','3','4'],correct:0};assert.equal(parseExamImport('```json\n'+JSON.stringify({questions:[q]})+'\n```')[0].text,'$x^2$');assert.throws(()=>parseExamImport(JSON.stringify({questions:[{...q,correct:5}]})));assert.throws(()=>parseExamImport('plain markdown'));assert.throws(()=>makeQuestions([{type:'essay',counts:[101,0,0,0]}]));});


test('matrix changes automatically reconcile types, levels and points without losing entered content',()=>{
 const original=[
  {id:'q-nb',rowId:'quiz',type:'quiz',level:'Nhận biết',points:.25,text:'Câu đã soạn',topic:'Số học',outcome:'Biết tính',answers:['A','B','C','D'],correct:2},
  {id:'q-vd',rowId:'quiz',type:'quiz',level:'Vận dụng',points:.25,text:'Câu vận dụng',topic:'Số học',outcome:'Vận dụng',answers:['1','2','3','4'],correct:1},
  {id:'tf-th',rowId:'truefalse',type:'truefalse',level:'Thông hiểu',points:1,text:'Đúng sai đã soạn',topic:'Hình học',outcome:'Hiểu',answers:['a','b','c','d'],correct:[true,false,true,false]}
 ];
 const rows=[
  {id:'quiz',type:'quiz',points:.5,topic:'Đại số',counts:[1,0,1,0]},
  {id:'truefalse',type:'truefalse',points:1,topic:'Hình học',counts:[0,1,0,0]}
 ];
 const first=syncQuestionsToMatrix(rows,original,[]);
 assert.equal(first.questions.length,3);
 assert.deepEqual(first.questions.map(q=>[q.type,q.level,q.points]),[
  ['quiz','Nhận biết',.5],['quiz','Vận dụng',.5],['truefalse','Thông hiểu',1]
 ]);
 assert.equal(first.questions[0].text,'Câu đã soạn');
 assert.deepEqual(first.questions[0].answers,['A','B','C','D']);
 assert.deepEqual(first.questions[2].correct,[true,false,true,false]);

 const reduced=syncQuestionsToMatrix([
  {id:'quiz',type:'quiz',points:.5,counts:[0,0,0,0]},
  rows[1]
 ],first.questions,first.archive);
 assert.equal(reduced.questions.length,1);
 assert.equal(reduced.archive.length,2);

 const restored=syncQuestionsToMatrix(rows,reduced.questions,reduced.archive);
 assert.equal(restored.questions.length,3);
 assert.equal(restored.questions.find(q=>q.id==='q-nb').text,'Câu đã soạn');
 assert.equal(restored.questions.find(q=>q.id==='q-vd').text,'Câu vận dụng');
});
