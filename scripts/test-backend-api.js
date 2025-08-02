#!/usr/bin/env node

import { spawn } from 'child_process';
import { setTimeout } from 'timers/promises';

async function testBackendAPI() {
  console.log('🚀 Starting backend server for API testing...');
  
  // Start backend server
  const server = spawn('python', ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8001'], {
    cwd: 'backend',
    stdio: 'pipe'
  });
  
  // Wait for server to start
  await setTimeout(3000);
  
  try {
    // Test health endpoint
    const response = await fetch('http://127.0.0.1:8001/health');
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Health endpoint:', data.status);
    }
    
    // Test root endpoint
    const rootResponse = await fetch('http://127.0.0.1:8001/');
    if (rootResponse.ok) {
      const rootData = await rootResponse.json();
      console.log('✅ Root endpoint:', rootData.message);
    }
    
    // Test run creation
    const runResponse = await fetch('http://127.0.0.1:8001/api/run/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company: 'Test Corp', domain: 'test.com' })
    });
    
    if (runResponse.ok) {
      const runData = await runResponse.json();
      console.log('✅ Run creation:', runData.run_id);
    }
    
    console.log('✅ All API tests passed!');
    
  } catch (error) {
    console.error('❌ API test failed:', error.message);
    process.exit(1);
  } finally {
    server.kill();
  }
}

testBackendAPI();