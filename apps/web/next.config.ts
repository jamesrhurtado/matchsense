import type { NextConfig } from 'next';
const config: NextConfig = {
  compress: false,
  output: 'standalone',
  // Keep `next dev` from mutating the production assets used by `next start`.
  distDir: process.env.NODE_ENV === 'development' ? '.next-dev' : '.next',
};
export default config;
