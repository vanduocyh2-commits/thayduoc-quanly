import {test} from 'node:test';import assert from 'node:assert/strict';import {uploadedQuestions,keysFromRows,structureFromKeys,defaultUploadStructure} from './client/uploadExam.mjs';
test('manual keys map four forms to exact points and reject missing answers',()=>{const s=[{type:'quiz',count:1,points:2},{type:'truefalse',count:1,points:2},{type:'short',count:1,points:2},{type:'essay',count:1,points:4}];const q=uploadedQuestions(s,{quiz:'B',truefalse:'Đ S Đ S',short:'2,5'});assert.equal(q.questions[0].correct,1);assert.deepEqual(q.questions[1].correct,[true,false,true,false]);assert.equal(q.questions[2].correct,'2,5');assert.equal(q.essays[0].points,4);assert.throws(()=>uploadedQuestions(s,{quiz:'A',truefalse:'Đ S',short:'2'}));assert.throws(()=>uploadedQuestions(s,{quiz:'E',truefalse:'Đ S Đ S',short:'2'}));});
test('spreadsheet keys remain separated by code and reject gaps and duplicates',()=>{const k=keysFromRows([{code:'101',type:'quiz',number:1,answer:'A'},{code:'102',type:'quiz',number:1,answer:'C'}]);assert.equal(k['101'].quiz,'A');assert.equal(k['102'].quiz,'C');assert.throws(()=>keysFromRows([{code:'101',type:'quiz',number:2,answer:'A'}]));assert.throws(()=>keysFromRows([{code:'101',type:'quiz',number:1,answer:'A'},{code:'101',type:'quiz',number:1,answer:'B'}]));});
test('TN Maker counts follow imported keys while retaining configured points and essays',()=>{
 const defaults=defaultUploadStructure();assert.equal(defaults.reduce((sum,r)=>sum+r.count*r.points,0),10);
 const keys={'101':{quiz:'A C',truefalse:'Đ Đ S S',short:'0,25\n0123'},'102':{quiz:'C B',truefalse:'S S Đ Đ',short:'-5\n0'}};
 const structure=structureFromKeys(defaults,keys);
 assert.deepEqual(structure.map(r=>r.count),[2,1,2,0]);
 assert.deepEqual(structure.map(r=>r.points),defaults.map(r=>r.points));
 assert.equal(structureFromKeys([{type:'essay',count:2,points:1}],keys)[0].count,2);
 const scored=uploadedQuestions(structure.map(r=>({...r,points:r.type==='quiz'?2:r.type==='truefalse'?2:r.type==='short'?2:1})),keys['101']);
 assert.deepEqual(scored.questions[2].correct,[true,true,false,false]);assert.equal(scored.questions[3].correct,'0,25');
 assert.throws(()=>structureFromKeys(defaults,{}));
 assert.throws(()=>structureFromKeys(defaults,{...keys,'102':{...keys['102'],short:'1'}}));
});
