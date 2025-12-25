import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fetchDashboard, fetchRuns, fetchIncidents } from '../api';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [runs, setRuns] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  async function loadData() {
    try {
      const [statsData, runsData, incidentsData] = await Promise.all([
        fetchDashboard(),
        fetchRuns(24),
        fetchIncidents('OPEN')
      ]);
      setStats(statsData);
      setRuns(runsData);
      setIncidents(incidentsData);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load data:', error);
      setLoading(false);
    }
  }

  if (loading) {
    return <div style={styles.loading}>Loading...</div>;
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Pipeline Health</h1>
      
      {/* Stats Cards */}
      <div style={styles.statsGrid}>
        <StatCard 
          title="Last 24 Runs"
          value={stats?.total_runs_24h || 0}
          color="#667eea"
        />
        <StatCard 
          title="Success Rate"
          value={`${stats?.success_rate || 0}%`}
          color="#48bb78"
        />
        <StatCard 
          title="Failure Rate"
          value={`${stats?.failure_rate || 0}%`}
          color="#f56565"
        />
        <StatCard 
          title="Avg Duration"
          value={`${stats?.avg_duration_sec || 0}s`}
          color="#ed8936"
        />
      </div>

      {/* Open Incidents */}
      {incidents.length > 0 && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>🚨 Open Incidents ({incidents.length})</h2>
          <div style={styles.incidentsList}>
            {incidents.map(incident => (
              <Link 
                key={incident.incident_id} 
                to={`/incidents/${incident.incident_id}`}
                style={styles.incidentCard}
              >
                <div style={styles.incidentHeader}>
                  <span style={styles.incidentId}>{incident.incident_id}</span>
                  <span style={styles.incidentStatus}>{incident.status}</span>
                </div>
                <div style={styles.incidentTitle}>{incident.title}</div>
                <div style={styles.incidentTime}>
                  {new Date(incident.start_time).toLocaleString()}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Recent Runs */}
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Recent Runs</h2>
        <div style={styles.runsTable}>
          <div style={styles.tableHeader}>
            <div style={styles.headerCell}>Run ID</div>
            <div style={styles.headerCell}>Repository</div>
            <div style={styles.headerCell}>Template</div>
            <div style={styles.headerCell}>Status</div>
            <div style={styles.headerCell}>Duration</div>
            <div style={styles.headerCell}>Time</div>
          </div>
          {runs.map(run => (
            <Link 
              key={run.run_id} 
              to={`/runs/${run.run_id}`}
              style={styles.tableRow}
            >
              <div style={styles.cell}>{run.run_id.slice(0, 8)}</div>
              <div style={styles.cell}>{run.repo}</div>
              <div style={styles.cell}>{run.job_template}</div>
              <div style={styles.cell}>
                <StatusBadge status={run.status} />
              </div>
              <div style={styles.cell}>
                {run.duration_sec ? `${run.duration_sec}s` : '-'}
              </div>
              <div style={styles.cell}>
                {new Date(run.queued_at).toLocaleTimeString()}
              </div>
            </Link>
          ))}
        </div>
      </div>
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

function StatusBadge({ status }) {
  const colors = {
    SUCCEEDED: '#48bb78',
    FAILED: '#f56565',
    RUNNING: '#ed8936',
    QUEUED: '#4299e1',
  };
  
  return (
    <span style={{
      ...styles.statusBadge,
      background: colors[status] || '#718096',
    }}>
      {status}
    </span>
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
    marginBottom: '1rem',
    color: '#2d3748',
  },
  incidentsList: {
    display: 'grid',
    gap: '1rem',
  },
  incidentCard: {
    background: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    textDecoration: 'none',
    color: 'inherit',
    borderLeft: '4px solid #f56565',
    transition: 'transform 0.2s',
    ':hover': {
      transform: 'translateY(-2px)',
    },
  },
  incidentHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '0.5rem',
  },
  incidentId: {
    fontWeight: 'bold',
    color: '#667eea',
  },
  incidentStatus: {
    background: '#f56565',
    color: 'white',
    padding: '0.25rem 0.75rem',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: '600',
  },
  incidentTitle: {
    fontSize: '1.125rem',
    marginBottom: '0.5rem',
    color: '#2d3748',
  },
  incidentTime: {
    fontSize: '0.875rem',
    color: '#718096',
  },
  runsTable: {
    background: 'white',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    overflow: 'hidden',
  },
  tableHeader: {
    display: 'grid',
    gridTemplateColumns: '100px 1fr 150px 120px 100px 120px',
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
    gridTemplateColumns: '100px 1fr 150px 120px 100px 120px',
    padding: '1rem',
    borderBottom: '1px solid #e2e8f0',
    textDecoration: 'none',
    color: 'inherit',
    transition: 'background 0.2s',
    ':hover': {
      background: '#f7fafc',
    },
  },
  cell: {
    padding: '0 0.5rem',
    display: 'flex',
    alignItems: 'center',
  },
  statusBadge: {
    color: 'white',
    padding: '0.25rem 0.75rem',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
};

