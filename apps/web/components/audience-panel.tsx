import {ArrowLeft,Clock3,ScanLine} from 'lucide-react';
import {cn,Story,Variant,timecode} from '@/lib/api';
import {Button,Card,Tag} from './ui';

/** Focus uses verified roles only. Legacy packages without role metadata cannot establish involvement. */
export function relevantStories(stories:Story[],focus:string){
 return !focus?stories:stories.filter(story=>story.team_id===focus||story.passer_id===focus||story.receiver_id===focus);
}
export function StoryPicker({stories,selected,onSelect,producer=false}:{stories:Story[];selected:string;onSelect:(id:string)=>void;producer?:boolean}){
 return <div className={cn('space-y-2',producer?'border-b border-stone-100 p-3':'mt-5')} role="group" aria-label={producer?'Story queue moments':'Approved moments'}>{stories.map((item,index)=><button key={item.id} type="button" aria-pressed={selected===item.id} onClick={()=>onSelect(item.id)} className={cn('flex min-h-11 w-full items-center justify-between gap-3 rounded-lg border px-3 py-2 text-left text-sm',selected===item.id?'border-emerald-300 bg-emerald-50 text-emerald-950':'border-stone-200 bg-white text-stone-600 hover:bg-stone-50')}><span className="min-w-0"><span className="block font-medium">Moment {index+1} · {timecode(item.eligible_from_ms)}</span><span className="block text-xs">{item.title}</span></span><span className="shrink-0 text-xs capitalize">{item.approved&&item.status==='expired'?'Approved · archived':item.status}</span></button>)}</div>;
}
export function AudiencePanel({story,stories,variant,language,detail,focus,workflowPending,overlayId,onSelect,onEvidence,onRecap,onWholePlay,controls}:{story:Story|null|undefined;stories:Story[];variant:Variant|null;language:string;detail:string;focus:string;workflowPending:boolean;overlayId?:string|null;onSelect:(id:string)=>void;onEvidence:()=>void;onRecap:()=>void;onWholePlay:()=>void;controls:React.ReactNode}){
 return <Card className="p-5 md:p-6"><div className="flex flex-wrap items-start justify-between gap-2"><div><p className="mb-1 text-xs font-semibold text-emerald-800">THE EXPLANATION</p><h2 className="text-balance text-xl font-semibold">{story?'Understand this sequence':focus?'Your selected focus':workflowPending?'AI review in progress':'The next story is taking shape'}</h2></div><Tag>{story?(story.id===overlayId?'Approved · on air':'Approved · history'):workflowPending?'Reviewing evidence':'Watching the play'}</Tag></div>
 {focus&&!stories.length?<div className="mt-4"><p className="text-pretty text-base leading-relaxed">No approved involvement in this interval.</p><p className="mt-2 text-pretty text-xs leading-relaxed text-stone-500">Only verified passer, receiver, or possession-team involvement appears here. Older stories may lack that information.</p><Button className="mt-3" onClick={onWholePlay}><ArrowLeft size={14}/>Whole play</Button></div>:<p data-testid="audience-explanation" lang={language} className={cn('mt-4 text-pretty leading-relaxed',detail==='simple'?'text-lg':'text-sm text-stone-600')}>{variant?.text||(language==='es'?'Las explicaciones aparecerán después de la aprobación del productor.':'Explanations appear once the producer approves a supported story.')}</p>}
 <div className="mt-4 flex flex-wrap gap-2"><Button disabled={!story} onClick={onEvidence}><ScanLine size={15}/>Show why</Button><Button onClick={onRecap}><Clock3 size={15}/>Catch me up</Button></div>
 <div className="mt-5 border-t border-stone-100 pt-4">{controls}</div>
 {detail==='detail'&&<p className="mt-4 text-pretty text-xs leading-relaxed text-stone-500">Measures describe this sequence only. Open Show why for operands, observation windows, coverage and limitations.</p>}
 {stories.length>0&&<details className="mt-4" open><summary className="text-sm font-medium text-stone-600">{focus?'Relevant approved history':'Approved history'} · {stories.length}</summary><StoryPicker stories={stories} selected={story?.id||''} onSelect={onSelect}/></details>}
 </Card>;
}
