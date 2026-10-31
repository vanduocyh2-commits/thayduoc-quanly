import {test} from 'node:test';import assert from 'node:assert/strict';
import {subjectGroups} from './client/librarySubjects.mjs';
test('documents, outlines and exams are grouped by their subject with stable Unicode and whitespace',()=>{
 const entry=(id,subject)=>({id,data:{subject}}),groups=subjectGroups([entry('1',' Toán '),entry('2','TOÁN'),entry('3','Vật   lí'),entry('4','Toa\u0301n'),entry('5','')]);
 assert.equal(groups.length,3);assert.deepEqual(groups.find(g=>g.key==='toán').items.map(r=>r.id),['1','2','4']);assert.equal(groups.find(g=>g.key==='vật lí').subject,'Vật lí');assert.equal(groups.find(g=>g.key==='chưa xác định môn').items[0].id,'5');
});
