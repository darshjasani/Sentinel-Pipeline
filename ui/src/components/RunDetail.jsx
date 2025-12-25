import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchRun } from '../api';

export default function RunDetail() {
  const { runId } = useParams();
  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRun();
    const interval = setInterval(loadRun, 3000); // Refresh every 3 seconds
    return () => clearInterval(interval);
  }, [runId]);

  async function loadRun() {
    try {
      const data = await fetchRun(runId);
      setRun(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load run:', error);
      setLoading(false);
    }
  }

  if (loading) {
    return <div style={styles.loading}>Loading run details...</div>;
  }

  if (!run) {
    return <div style={styles.error}>Run not found</div>;
  }

  return (
    <div style={styles.container}>
      <Link to="/" style={styles.backLink}>← Back to Dashboard</Link>
      
      <div style={styles.header}>
        <h1 style={styles.title}>Run {run.run_id.slice(0, 8)}</h1>
        <StatusBadge status={run.status} />
      </div>

      {/* Run Info */}
      <div style={styles.infoGrid}>
        <InfoItem label="Repository" value={run.repo} />
        <InfoItem label="Template" value={run.job_template} />
        <InfoItem label="Triggered By" value={run.triggered_by || 'Unknown'} />
        <InfoItem label="Duration" value={run.duration_sec ? `${run.duration_sec}s` : 'N/A'} />
        <InfoItem label="Exit Code" value={run.exit_code !== null ? run.exit_code : 'N/A'} />
        <InfoItem label="Queued At" value={new Date(run.queued_at).toLocaleString()} />
      </div>

      {/* Failure Info */}
      {run.failure && (
        <div style={styles.failureSection}>
          <h2 style={styles.sectionTitle}>❌ Failure Information</h2>
          <div style={styles.failureCard}>
            <div style={styles.failureRow}>
              <span style={styles.failureLabel}>Category:</span>
              <span style={styles.failureValue}>{run.failure.category}</span>
            </div>
            {run.failure.cluster_id && (
              <div style={styles.failureRow}>
                <span style={styles.failureLabel}>Cluster ID:</span>
                <span style={styles.failureValue}>{run.failure.cluster_id}</span>
              </div>
            )}
            {run.failure.confidence && (
              <div style={styles.failureRow}>
                <span style={styles.failureLabel}>Confidence:</span>
                <span style={styles.failureValue}>
                  {(run.failure.confidence * 100).toFixed(0)}%
                </span>
              </div>
            )}
            {run.failure.message && (
              <div style={styles.failureMessage}>
                <div style={styles.failureLabel}>Error Message:</div>
                <pre style={styles.failureMessageText}>{run.failure.message}</pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Steps */}
      <div style={styles.stepsSection}>
        <h2 style={styles.sectionTitle}>Execution Steps</h2>
        <div style={styles.stepsList}>
          {run.steps.map((step, index) => (
            <div key={index} style={styles.stepCard}>
              <div style={styles.stepHeader}>
                <div style={styles.stepName}>
                  {getStepIcon(step.status)} {step.step_name}
                </div>
                <StatusBadge status={step.status} />
              </div>
              <div style={styles.stepDetails}>
                {step.duration_sec !== null && (
                  <span style={styles.stepDetail}>Duration: {step.duration_sec}s</span>
                )}
                {step.exit_code !== null && (
                  <span style={styles.stepDetail}>Exit Code: {step.exit_code}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    SUCCEEDED: '#48bb78',
    FAILED: '#f56565',
    RUNNING: '#ed8936',
    QUEUED: '#4299e1',
    PENDING: '#a0aec0',
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

function InfoItem({ label, value }) {
  return (
    <div style={styles.infoItem}>
      <div style={styles.infoLabel}>{label}</div>
      <div style={styles.infoValue}>{value}</div>
    </div>
  );
}

function getStepIcon(status) {
  const icons = {
    SUCCEEDED: '✅',
    FAILED: '❌',
    RUNNING: '⏳',
    PENDING: '⏸️',
  };
  return icons[status] || '○';
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
  error: {
    textAlign: 'center',
    padding: '3rem',
    fontSize: '1.2rem',
    color: '#f56565',
  },
  backLink: {
    display: 'inline-block',
    marginBottom: '1.5rem',
    color: '#667eea',
    textDecoration: 'none',
    fontWeight: '500',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '2rem',
  },
  title: {
    fontSize: '2rem',
    fontWeight: 'bold',
    color: '#2d3748',
  },
  statusBadge: {
    color: 'white',
    padding: '0.5rem 1rem',
    borderRadius: '20px',
    fontSize: '0.875rem',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  infoGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '1rem',
    marginBottom: '2rem',
  },
  infoItem: {
    background: 'white',
    padding: '1rem',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  infoLabel: {
    fontSize: '0.875rem',
    color: '#718096',
    marginBottom: '0.25rem',
  },
  infoValue: {
    fontSize: '1.125rem',
    fontWeight: '600',
    color: '#2d3748',
  },
  failureSection: {
    marginBottom: '2rem',
  },
  sectionTitle: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    marginBottom: '1rem',
    color: '#2d3748',
  },
  failureCard: {
    background: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    borderLeft: '4px solid #f56565',
  },
  failureRow: {
    display: 'flex',
    marginBottom: '0.75rem',
  },
  failureLabel: {
    fontWeight: '600',
    color: '#4a5568',
    minWidth: '120px',
  },
  failureValue: {
    color: '#2d3748',
  },
  failureMessage: {
    marginTop: '1rem',
    paddingTop: '1rem',
    borderTop: '1px solid #e2e8f0',
  },
  failureMessageText: {
    marginTop: '0.5rem',
    padding: '1rem',
    background: '#f7fafc',
    borderRadius: '4px',
    fontSize: '0.875rem',
    overflow: 'auto',
    maxHeight: '300px',
  },
  stepsSection: {
    marginBottom: '2rem',
  },
  stepsList: {
    display: 'grid',
    gap: '1rem',
  },
  stepCard: {
    background: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  stepHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.75rem',
  },
  stepName: {
    fontSize: '1.125rem',
    fontWeight: '600',
    color: '#2d3748',
  },
  stepDetails: {
    display: 'flex',
    gap: '1.5rem',
    fontSize: '0.875rem',
    color: '#718096',
  },
  stepDetail: {},
};

