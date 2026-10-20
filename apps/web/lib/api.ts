import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
export const cn = (...values: ClassValue[]) => twMerge(clsx(values));
export type Player = { id:string; team_id:string; name:string; number:number };
export type Frame = { players: { player_id:string; team_id:string; x_m:number; y_m:number }[]; ball:{ x_m:number; y_m:number }|null; controlling_player_id:string|null; possession_team_id:string|null };
export type Story = { id:string; revision:number; title:string; evidence_revision:string; eligible_from_ms:number; expires_at_ms:number; status:string; package_hash?:string };
export type Match = { session_id:string; clock_ms:number; duration_ms:number; running:boolean; speed:number; mode:string; story:Story|null; story_status:string; overlay:string|null; delivered_count:number; frame:Frame|null; teams:{id:string;name:string;color:string}[]; players:Player[]; cursor:number; };
export type Metrics = { pressure_opponents_max:number; pressure_radius_m:number; pressure_samples:number; bypassed_count:number; bypassed_player_ids:string[]; progression_m:number; retention_window_ms:number; coverage:number; source_message_ids:string[]; limitations:string[]; pass_start:{x_m:number;y_m:number}; pass_end:{x_m:number;y_m:number}; passer_id:string; receiver_id:string; };
export type Variant = { id:string; text:string; language:string; detail:string; focus:string|null; };
export type Evidence = { cutoff_ms:number; frames:{time_ms:number;payload:Frame;message_id:string}[]; story:{ id:string; revision:number; package_hash:string; evidence_revision:string; metrics:Metrics; variants:Variant[]; mode:string; review:{status:string;reason:string;proposed_text:string|null;revised_text:string;cycles:number}; workflow_ms:number; trace:{role:string;action:string;status:string;elapsed_ms:number}[]; }; };
export type Recap = { title:string; through_ms:number; moments:{story_id:string;revision:number;text:string}[]; };
export const timecode=(ms:number) => `${Math.floor(ms/60000).toString().padStart(2,'0')}:${Math.floor(ms/1000)%60 < 10 ? '0' : ''}${Math.floor(ms/1000)%60}`;
export function token() { return typeof window!=='undefined' ? sessionStorage.getItem('why-now-token') || '' : ''; }
export async function api<T>(path:string, options:RequestInit={}, protectedCall=false):Promise<T> {
 const response=await fetch(`/api${path}`,{...options,headers:{'Content-Type':'application/json',...(protectedCall?{'X-Producer-Token':token()}:{}),...options.headers},cache:'no-store'});
 if(!response.ok){ const body=await response.json().catch(()=>({})); throw new Error(body.detail?.code?.replaceAll('_',' ') || `Request failed (${response.status})`); }
 return response.json();
}
