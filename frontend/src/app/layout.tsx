import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { QueryProvider } from './providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'VentureCompass AI | Startup Intelligence Platform',
  description: 'AI-powered startup intelligence with 8-agent multi-phase analysis using complete Tavily API integration.',
  keywords: ['startup intelligence', 'AI analysis', 'venture capital', 'company research', 'Tavily API'],
  authors: [{ name: 'VentureCompass AI' }],
  viewport: 'width=device-width, initial-scale=1',
  robots: 'index, follow',
  openGraph: {
    title: 'VentureCompass AI | Startup Intelligence Platform',
    description: 'AI-powered startup intelligence with 8-agent multi-phase analysis',
    type: 'website',
    url: 'https://venturecompass.ai',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'VentureCompass AI',
    description: 'AI-powered startup intelligence platform',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className} suppressHydrationWarning>
        <QueryProvider>
          <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
            <main className="container mx-auto px-4 py-8">
              {children}
            </main>
          </div>
        </QueryProvider>
      </body>
    </html>
  )
}