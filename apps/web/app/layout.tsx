import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'WHY/NOW — Understand the moment', description: 'Evidence-first synthetic football story director.' };
export default function Layout({children}:{children:React.ReactNode}) { return <html lang="en"><body>{children}</body></html>; }
