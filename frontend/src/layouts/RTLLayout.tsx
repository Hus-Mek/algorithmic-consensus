import type { ReactNode } from 'react';
import Navbar from '../components/Navbar';

interface Props {
  children: ReactNode;
}

export default function RTLLayout({ children }: Props) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <main style={{
        flex: 1,
        maxWidth: '920px',
        width: '100%',
        margin: '0 auto',
        padding: '24px 16px 80px',
      }}>
        {children}
      </main>
    </div>
  );
}
