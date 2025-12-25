import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import RunDetail from './components/RunDetail';
import IncidentDetail from './components/IncidentDetail';
import FlakyTests from './components/FlakyTests';

export default function App() {
  return (
    <BrowserRouter>
      <div style={styles.container}>
        <nav style={styles.nav}>
          <div style={styles.navContent}>
            <h1 style={styles.logo}>⚡ Sentinel Pipeline</h1>
            <div style={styles.navLinks}>
              <Link to="/" style={styles.navLink}>Dashboard</Link>
              <Link to="/flaky-tests" style={styles.navLink}>Flaky Tests</Link>
            </div>
          </div>
        </nav>
        
        <main style={styles.main}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/runs/:runId" element={<RunDetail />} />
            <Route path="/incidents/:incidentId" element={<IncidentDetail />} />
            <Route path="/flaky-tests" element={<FlakyTests />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    background: '#f5f5f5',
  },
  nav: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    padding: '1rem 2rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  navContent: {
    maxWidth: '1400px',
    margin: '0 auto',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logo: {
    color: 'white',
    fontSize: '1.5rem',
    fontWeight: 'bold',
  },
  navLinks: {
    display: 'flex',
    gap: '2rem',
  },
  navLink: {
    color: 'white',
    textDecoration: 'none',
    fontWeight: '500',
    transition: 'opacity 0.2s',
    ':hover': {
      opacity: 0.8,
    },
  },
  main: {
    maxWidth: '1400px',
    margin: '2rem auto',
    padding: '0 2rem',
  },
};

