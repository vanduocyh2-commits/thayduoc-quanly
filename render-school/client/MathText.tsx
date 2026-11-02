import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
// MathML uses the browser's native math renderer; no remote scripts or font downloads.
export default function MathText({text='',inline=false}:any){
 const source=String(text).replace(/\\\[([\s\S]*?)\\\]/g,(_,math)=>'\n$$\n'+math+'\n$$\n').replace(/\\\(([\s\S]*?)\\\)/g,(_,math)=>'$'+math+'$');
 return <div className={'math-text'+(inline?' math-inline':'')}><ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[[rehypeKatex,{output:'mathml',trust:false,strict:'ignore',throwOnError:false}]]} components={{a:({href,children})=><a href={href} target="_blank" rel="noopener noreferrer">{children}</a>}}>{source}</ReactMarkdown></div>;
}
