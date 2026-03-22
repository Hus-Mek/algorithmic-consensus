import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import ar from '../i18n/ar';

export default function Navbar() {
  const location = useLocation();
  const isDashboard = location.pathname === '/dashboard';
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav style={{
      background: 'rgba(26, 26, 46, 0.92)',
      borderBottom: '1px solid var(--border-color)',
      padding: '12px 24px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      backdropFilter: 'blur(12px)',
    }}>
      <Link to="/" style={{ textDecoration: 'none' }}>
        <h1 style={{
          fontSize: '1.2rem',
          fontWeight: 700,
          color: 'var(--accent-blue)',
          margin: 0,
        }}>
          {ar.appName}
        </h1>
      </Link>

      {/* Hamburger for mobile */}
      <button
        className="hamburger"
        onClick={() => setMenuOpen(!menuOpen)}
        aria-label="Menu"
      >
        <span />
        <span />
        <span />
      </button>

      {/* Nav links */}
      <div className={`nav-links ${menuOpen ? 'open' : ''}`}>
        <Link to="/" onClick={() => setMenuOpen(false)}>
          <button style={{
            background: !isDashboard ? 'var(--accent-blue)' : 'transparent',
            color: !isDashboard ? 'var(--bg-primary)' : 'var(--text-secondary)',
            border: !isDashboard ? 'none' : '1px solid var(--border-color)',
            padding: '7px 18px',
            fontSize: '0.9rem',
          }}>
            {ar.navParticipant}
          </button>
        </Link>
        <Link to="/dashboard" onClick={() => setMenuOpen(false)}>
          <button style={{
            background: isDashboard ? 'var(--accent-blue)' : 'transparent',
            color: isDashboard ? 'var(--bg-primary)' : 'var(--text-secondary)',
            border: isDashboard ? 'none' : '1px solid var(--border-color)',
            padding: '7px 18px',
            fontSize: '0.9rem',
          }}>
            {ar.navDashboard}
          </button>
        </Link>
      </div>
    </nav>
  );
}
