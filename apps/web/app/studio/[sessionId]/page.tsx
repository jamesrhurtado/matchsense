import MatchDesk from '@/components/match-desk';
export default async function Page({params}:{params:Promise<{sessionId:string}>}){const {sessionId}=await params;return <MatchDesk id={sessionId} mode="studio"/>;}
