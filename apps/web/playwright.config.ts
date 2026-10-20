import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests',timeout:45000,use:{baseURL:'http://127.0.0.1:3000',headless:true,channel:process.env.PLAYWRIGHT_CHANNEL},workers:1,reporter:'list'});
