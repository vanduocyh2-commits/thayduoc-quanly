export async function downloadExam(courseId:string,data:any,csrf:string,format='zip'){
 const r=await fetch('/api/exams/export',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify({courseId,data,format})});
 if(!r.ok){const d=await r.json();throw Error(d.error||'Không xuất được tệp.');}
 const url=URL.createObjectURL(await r.blob());const a=document.createElement('a');a.href=url;a.download=format==='outline'?'de-cuong.docx':'bo-de-kiem-tra.zip';a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);
}
