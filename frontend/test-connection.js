#!/usr/bin/env node

// Simple script to test backend connection
const axios = require('axios');

// Load environment variables
require('dotenv').config({ path: '.env.local' });

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://0.0.0.0:8000/api';

async function testConnection() {
  console.log('🔧 Testing backend connection...');
  console.log(`📡 Backend URL: ${API_BASE_URL}`);
  
  try {
    // Test basic connection - try to access the root API
    console.log('\n1️⃣ Testing basic API connectivity...');
    const rootUrl = API_BASE_URL.replace('/api', '');
    const response = await axios.get(`${rootUrl}/docs`, {
      timeout: 10000,
      validateStatus: (status) => status < 500 // Accept redirects, etc.
    });
    
    console.log('✅ SUCCESS! Backend is reachable');
    console.log(`📊 Response status: ${response.status}`);
    
    // Try the API root
    console.log('\n2️⃣ Testing API root...');
    try {
      const apiResponse = await axios.get(`${API_BASE_URL}`, {
        timeout: 5000,
        validateStatus: (status) => status < 500
      });
      console.log(`📡 API root status: ${apiResponse.status}`);
    } catch (apiError) {
      console.log(`📡 API root: ${apiError.response?.status || 'No response'}`);
    }
    
  } catch (error) {
    console.log('❌ FAILED! Backend connection error');
    
    if (error.code === 'ECONNREFUSED') {
      console.log('🔥 Connection refused - is the backend running?');
      console.log(`   Start backend with: cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`);
    } else if (error.code === 'ETIMEDOUT') {
      console.log('⏰ Connection timeout - backend may be slow to respond');
    } else {
      console.log(`🐛 Error: ${error.message}`);
      if (error.response) {
        console.log(`📝 Status: ${error.response.status}`);
        console.log(`📄 Response: ${JSON.stringify(error.response.data, null, 2)}`);
      }
    }
  }
}

// Run the test
testConnection();