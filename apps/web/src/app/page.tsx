'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { Dashboard } from '@/components/Dashboard';

export default function Home() {
  const { user, ready } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (ready && !user) {
      router.replace('/login');
    }
  }, [ready, user, router]);

  if (!ready) {
    return (
      <div className="h-screen flex items-center justify-center bg-command-bg">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
          <p className="text-gray-400 text-sm">Loading ResQGrid AI...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="h-screen flex items-center justify-center bg-command-bg">
        <p className="text-gray-400 text-sm">Redirecting to login...</p>
      </div>
    );
  }

  return <Dashboard />;
}
