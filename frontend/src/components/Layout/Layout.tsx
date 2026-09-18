import React, { ReactNode, memo } from 'react';
import Header from './Header';
import { useLocation } from 'react-router-dom';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = memo(({ children }) => {
  const eventPage = useLocation().pathname === '/event';
  return (
    <div className={`min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-150 ${eventPage ? 'event-layout' : ''}`}>
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
});

export default Layout;
