import type { NextConfig } from 'next'

// Get backend URL from environment, fallback to default
const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://0.0.0.0:8000/api';
const backendBaseUrl = backendUrl.replace('/api', ''); // Remove /api suffix for rewrite

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ['lucide-react']
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendBaseUrl}/api/:path*`
      }
    ]
  },
  // Ensure environment variables are available
  env: {
    BACKEND_URL: backendBaseUrl,
  }
}

export default nextConfig