import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fetchFlakyTests } from '../api';

export default function FlakyTests() {
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTests();
    const interval = setInterval(loadTests, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  async function loadTests() {
    try {
      const data = await fetchFlakyTests();
      setTests(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load flaky tests:', error);
      setLoading(false);
    }
  }

  if (loading) {
    return <div style={styles.loading}>Loading flaky tests...</div>;
  }

  const flakyTests = tests.filter(t => t.is_flaky);
  const deterministicTests = tests.filter(t => !t.is_flaky && t.failure_rate >= 90);

  return (
    <div style={styles.container}>
      <Link to="/" style={styles.backLink}>← Back to Dashboard</Link>
      
      <h1 style={styles.title}>🧪 Test Analysis</h1>

      {/* Summary Stats */}
      <div style={styles.statsGrid}>
        <StatCard 
          title="Flaky Tests Detected"
          value={flakyTests.length}
          color="#ed8936"
        />
        <StatCard 
          title="Deterministic Failures"
          value={deterministicTests.length}
          color="#f56565"
        />
        <StatCard 
          title="Total Tests Tracked"
          value={tests.length}
          color="#667eea"
        />
      </div>

      {/* Flaky Tests */}
      {flakyTests.length > 0 && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>🟡 Flaky Tests</h2>
          <p style={styles.sectionDescription}>
            Tests with inconsistent results (10-90% failure rate)
          </p>
          <div style={styles.table}>
            <div style={styles.tableHeader}>
              <div style={styles.headerCell}>Test Name</div>
              <div style={styles.headerCell}>Repository</div>
              <div style={styles.headerCell}>Failure Rate</div>
              <div style={styles.headerCell}>Total Runs</div>
              <div style={styles.headerCell}>Failed Runs</div>
            </div>
            {flakyTests.map((test, index) => (
              <div key={index} style={styles.tableRow}>
                <div style={styles.cell}>
                  <span style={styles.testName}>{test.test_name}</span>
                </div>
                <div style={styles.cell}>{test.repo_id}</div>
                <div style={styles.cell}>
                  <FailureRateBar rate={test.failure_rate} />
                </div>
                <div style={styles.cell}>{test.total_runs}</div>
                <div style={styles.cell}>
                  {test.failed_runs} / {test.total_runs}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Deterministic Failures */}
      {deterministicTests.length > 0 && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>🔴 Deterministic Failures</h2>
          <p style={styles.sectionDescription}>
            Tests that consistently fail (≥90% failure rate)
          </p>
          <div style={styles.table}>
            <div style={styles.tableHeader}>
              <div style={styles.headerCell}>Test Name</div>
              <div style={styles.headerCell}>Repository</div>
              <div style={styles.headerCell}>Failure Rate</div>
              <div style={styles.headerCell}>Total Runs</div>
              <div style={styles.headerCell}>Failed Runs</div>
            </div>
            {deterministicTests.map((test, index) => (
              <div key={index} style={styles.tableRow}>
                <div style={styles.cell}>
                  <span style={styles.testName}>{test.test_name}</span>
                </div>
                <div style={styles.cell}>{test.repo_id}</div>
                <div style={styles.cell}>
                  <FailureRateBar rate={test.failure_rate} />
                </div>
                <div style={styles.cell}>{test.total_runs}</div>
                <div style={styles.cell}>
                  {test.failed_runs} / {test.total_runs}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tests.length === 0 && (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>📊</div>
          <div style={styles.emptyText}>No test data available yet</div>
          <div style={styles.emptySubtext}>
            Run some CI jobs to see test analysis
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ title, value, color }) {
  return (
    <div style={{...styles.statCard, borderLeft: `4px solid ${color}`}}>
      <div style={styles.statTitle}>{title}</div>
      <div style={{...styles.statValue, color}}>{value}</div>
    </div>
  );
}

function FailureRateBar({ rate }) {
  const color = rate >= 90 ? '#f56565' : rate >= 10 ? '#ed8936' : '#48bb78';
  
  return (
    <div style={styles.rateContainer}>
      <div style={styles.rateBar}>
        <div style={{
          ...styles.rateBarFill,
          width: `${rate}%`,
          background: color,
        }}></div>
      </div>
      <span style={styles.rateText}>{rate.toFixed(1)}%</span>
    </div>
  );
}

const styles = {
  container: {
    paddingBottom: '3rem',
  },
  loading: {
    textAlign: 'center',
    padding: '3rem',
    fontSize: '1.2rem',
    color: '#718096',
  },
  backLink: {
    display: 'inline-block',
    marginBottom: '1.5rem',
    color: '#667eea',
    textDecoration: 'none',
    fontWeight: '500',
  },
  title: {
    fontSize: '2rem',
    fontWeight: 'bold',
    marginBottom: '2rem',
    color: '#2d3748',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '1.5rem',
    marginBottom: '3rem',
  },
  statCard: {
    background: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  statTitle: {
    fontSize: '0.875rem',
    color: '#718096',
    marginBottom: '0.5rem',
    fontWeight: '500',
  },
  statValue: {
    fontSize: '2rem',
    fontWeight: 'bold',
  },
  section: {
    marginBottom: '3rem',
  },
  sectionTitle: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    marginBottom: '0.5rem',
    color: '#2d3748',
  },
  sectionDescription: {
    color: '#718096',
    marginBottom: '1rem',
  },
  table: {
    background: 'white',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    overflow: 'hidden',
  },
  tableHeader: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr 200px 100px 150px',
    background: '#f7fafc',
    padding: '1rem',
    fontWeight: '600',
    fontSize: '0.875rem',
    color: '#4a5568',
    borderBottom: '1px solid #e2e8f0',
  },
  headerCell: {
    padding: '0 0.5rem',
  },
  tableRow: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr 200px 100px 150px',
    padding: '1rem',
    borderBottom: '1px solid #e2e8f0',
  },
  cell: {
    padding: '0 0.5rem',
    display: 'flex',
    alignItems: 'center',
  },
  testName: {
    fontFamily: 'monospace',
    fontSize: '0.875rem',
    color: '#2d3748',
  },
  rateContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    width: '100%',
  },
  rateBar: {
    flex: 1,
    height: '8px',
    background: '#e2e8f0',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  rateBarFill: {
    height: '100%',
    transition: 'width 0.3s ease',
  },
  rateText: {
    fontSize: '0.875rem',
    fontWeight: '600',
    minWidth: '50px',
    textAlign: 'right',
  },
  emptyState: {
    textAlign: 'center',
    padding: '4rem 2rem',
    background: 'white',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  emptyIcon: {
    fontSize: '4rem',
    marginBottom: '1rem',
  },
  emptyText: {
    fontSize: '1.25rem',
    fontWeight: '600',
    color: '#2d3748',
    marginBottom: '0.5rem',
  },
  emptySubtext: {
    color: '#718096',
  },
};

