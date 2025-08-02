#!/usr/bin/env node

import { existsSync } from 'fs';
import { spawn } from 'child_process';
import { promisify } from 'util';

const exec = promisify(spawn);

function checkFile(path, name) {
  return existsSync(path) ? '✅' : '❌';
}

async function checkService(url, name) {
  try {
    const response = await fetch(url);
    return response.ok ? '✅ Running' : '❌ Error';
  } catch {
    return '❌ Not running';
  }
}

async function showStatus() {
  console.log('\n🎯 VentureCompass AI Project Status\n');
  
  console.log('📁 Project Structure:');
  console.log(`   Backend: ${checkFile('backend', 'backend')}`);
  console.log(`   Frontend: ${checkFile('frontend', 'frontend')}`);
  console.log(`   Root package.json: ${checkFile('package.json', 'package.json')}`);
  
  console.log('\n🔧 Environment:');
  console.log(`   Backend .env: ${checkFile('backend/.env', 'backend .env')}`);
  console.log(`   Frontend .env: ${checkFile('frontend/.env', 'frontend .env')}`);
  console.log(`   Backend venv: ${checkFile('backend/.venv', 'backend venv')}`);
  console.log(`   Frontend node_modules: ${checkFile('frontend/node_modules', 'frontend node_modules')}`);
  console.log(`   Root node_modules: ${checkFile('node_modules', 'root node_modules')}`);
  
  console.log('\n🚀 Services:');
  console.log(`   Backend (8000): ${await checkService('http://localhost:8000/health', 'backend')}`);
  console.log(`   Frontend (5173): ${await checkService('http://localhost:5173', 'frontend')}`);
  
  console.log('\n📖 Available commands:');
  console.log('   npm run dev          # Start both servers');
  console.log('   npm run setup        # Set up environment');
  console.log('   npm run test         # Run all tests');
  console.log('   npm run build        # Build for production');
  console.log('   npm run clean        # Clean artifacts');
  
  console.log('\n🔗 URLs (when running):');
  console.log('   Backend API: http://localhost:8000');
  console.log('   Frontend:    http://localhost:5173');
  console.log('   API Docs:    http://localhost:8000/docs');
}

showStatus();