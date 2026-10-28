import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'MatchSense — Understand the moment', description: 'Clear football explanations grounded in match data, as the game unfolds.' };
export default function Layout({children}:{children:React.ReactNode}) { return <html lang="en"><body>{children}</body></html>; }
