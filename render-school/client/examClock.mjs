export function remainingSeconds(deadline,now){return Number.isFinite(deadline)?Math.max(0,Math.ceil((deadline-now)/1000)):null;}
export function clockText(seconds){const n=Math.max(0,Math.floor(seconds));return [Math.floor(n/3600),Math.floor(n/60)%60,n%60].map(v=>String(v).padStart(2,'0')).join(':');}
