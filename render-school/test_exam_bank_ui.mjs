import {test} from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {createServer} from 'vite';
test('bank assignment opens without undefined editor state; guide belongs to source editor',async()=>{
 const vite=await createServer({server:{middlewareMode:true},appType:'custom'});
 try{
  const {AssignBankExam,default:ExamBankEditor}=await vite.ssrLoadModule('/client/ExamBankEditor.tsx');
  const record={id:'exam1',data:{title:'Đề kiểm tra',grade:'12',questions:[],essays:[],answerGuide:'Hướng dẫn đã lưu'}};
  const courses=[{id:'c1',name:'12A1',subject:'Toán',grade:'12'}];
  const html=renderToStaticMarkup(React.createElement(AssignBankExam,{record,courses,act:async()=>true,close:()=>{}}));
  assert.match(html,/Giao bài cho lớp/);assert.match(html,/12A1/);assert.match(html,/name="courseId"/);assert.match(html,/name="gradingMode"/);assert.doesNotMatch(html,/Hướng dẫn giải chi tiết/);
  const editor=renderToStaticMarkup(React.createElement(ExamBankEditor,{record,csrf:'test',reload:async()=>{},notify:()=>{},close:()=>{}}));
  assert.match(editor,/Hướng dẫn giải chi tiết/);assert.match(editor,/Hướng dẫn đã lưu/);
 }finally{await vite.close()}
});
