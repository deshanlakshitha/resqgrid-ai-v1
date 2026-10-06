import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/lib/auth';
import { ServiceWorkerRegister } from '@/components/ServiceWorkerRegister';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'ResQGrid AI — Command Center',
  description: 'Intelligent Emergency Resource Network',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'ResQGrid AI',
  },
  icons: {
    icon: ['/icons/icon-192x192.png'],
    apple: ['/icons/icon-192x192.png'],
  },
};

export const viewport: Viewport = {
  themeColor: '#0f172a',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`dark ${inter.variable}`}>
      <body className="bg-command-bg text-command-text font-sans antialiased">
        <AuthProvider>
          {children}
          <ServiceWorkerRegister />
        </AuthProvider>
      </body>
    </html>
  );
}
