import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'MatchSense — Understand the moment', description: 'Evidence-backed explanations for football fans, as the match unfolds.' };
export default function Layout({children}:{children:React.ReactNode}) { return <html lang="en"><body>{children}</body></html>; }
