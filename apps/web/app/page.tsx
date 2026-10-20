'use client';
import {useState} from 'react';
import {useRouter} from 'next/navigation';
import {ArrowUpRight, ArrowRight, Radio, ShieldCheck, ScanLine} from 'lucide-react';
import {api} from '@/lib/api';
import {Button,Tag} from '@/components/ui';
export default function Home(){
 const router=useRouter();const [key,setKey]=useState('local-demo-producer');const [fixture,setFixture]=useState('match-001');const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 async function create(){setBusy(true);setError('');sessionStorage.setItem('why-now-token',key);try{const data=await api<{session_id:string}>('/replay-sessions',{method:'POST',body:JSON.stringify({match_id:fixture})},true);router.push(`/studio/${data.session_id}`);}catch(e){setError((e as Error).message);setBusy(false);}}
 return <main className="mx-auto flex min-h-dvh max-w-6xl flex-col px-6 py-8 md:px-12">
  <header className="flex items-center justify-between"><a href="/" className="text-xl font-black">WHY<span className="text-emerald-700">/</span>NOW</a><Tag><span className="size-1.5 rounded-full bg-emerald-700"/>Working local prototype</Tag></header>
  <div className="grid flex-1 items-center gap-14 py-16 lg:grid-cols-2">
   <section><p className="mb-6 text-sm font-semibold text-emerald-800">THE STORY BEHIND THE PLAY</p><h1 className="max-w-xl text-balance text-5xl font-semibold leading-tight md:text-6xl">See the play.<br/>Understand<br/>the moment.</h1><p className="mt-7 max-w-md text-pretty text-lg leading-relaxed text-stone-500">The shot gets the attention. We help you explain the pass before it—with evidence you can inspect and a story you control.</p><div className="mt-10 flex gap-6 text-sm text-stone-600"><span className="flex items-center gap-2"><ScanLine size={17}/>Inspectable evidence</span><span className="flex items-center gap-2"><ShieldCheck size={17}/>Producer approved</span></div></section>
   <section className="rounded-3xl border border-stone-200 bg-white p-8 shadow-sm md:p-10"><div className="mb-8 flex items-start justify-between"><div><Tag className="bg-emerald-50 text-emerald-800"><Radio size={12}/>Synthetic match replay</Tag><h2 className="mt-4 text-balance text-2xl font-semibold">Your production desk</h2></div><ArrowUpRight size={22} className="text-stone-400"/></div><p className="mb-8 text-pretty text-sm leading-relaxed text-stone-500">Open an isolated match session. Inspect a pressure escape, approve its explanation, and share the companion view.</p>
    <label htmlFor="fixture" className="mb-2 block text-sm font-medium">Replay segment</label><select id="fixture" value={fixture} onChange={e=>setFixture(e.target.value)} className="mb-5 min-h-12 w-full rounded-lg border border-stone-200 bg-stone-50 px-3 text-sm"><option value="match-001">01 · Harbor City vs Alder Rovers</option><option value="match-002">02 · Second synthetic segment</option><option value="match-003">03 · Third synthetic segment</option></select>
    <label htmlFor="access" className="mb-2 block text-sm font-medium">Producer access key</label><input id="access" value={key} onChange={e=>setKey(e.target.value)} type="password" className="min-h-12 w-full rounded-lg border border-stone-200 px-3 text-sm"/><p className="mt-2 text-xs text-stone-400">Local demo key is prefilled. Each session has its own clock and approvals.</p>
    {error&&<p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}<Button tone="primary" disabled={busy} onClick={create} className="mt-7 w-full py-3">{busy?'Opening your desk…':'Open producer console'}<ArrowRight size={17}/></Button>
    <div className="mt-7 border-t border-stone-100 pt-5 text-xs leading-relaxed text-stone-400">Fictional teams. Original synthetic data. Local explanations use validated templates. Azure and model execution are pending.</div>
   </section>
  </div><footer className="flex flex-wrap justify-between gap-3 border-t border-stone-200 pt-5 text-xs text-stone-400"><span>WHY/NOW · Evidence-first match stories</span><span>Ingest → interpret → explain → approve → share</span></footer>
 </main>;
}
