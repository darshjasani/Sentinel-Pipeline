import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchIncident } from '../api';

export default function IncidentDetail() {
  const { incidentId } = useParams();
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadIncident();
  }, [incidentId]);

  async function loadIncident() {
    try {
      const data = await fetchIncident(incidentId);
      setIncident(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load incident:', error);
      setLoading(false);
    }
  }

  if (loading) {
    return <div style={styles.loading}>Loading incident details...</div>;
  }

  if (!incident) {
    return <div style={styles.error}>Incident not found</div>;
  }

  return (
    <div style={styles.container}>
      <Link to="/" style={styles.backLink}>← Back to Dashboard</Link>
      
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>{incident.incident_id}</h1>
          <div style={styles.subtitle}>{incident.title}</div>
        </div>
        <StatusBadge status={incident.status} />
      </div>

      {/* Impact and Root Cause */}
      <div style={styles.mainInfo}>
        <div style={styles.infoCard}>
          <h3 style={styles.infoCardTitle}>💥 Impact</h3>
          <p style={styles.infoCardText}>
            {incident.impact_summary || 'No impact summary available'}
          </p>
        </div>
        
        <div style={styles.infoCard}>
          <h3 style={styles.infoCardTitle}>🔍 Suspected Root Cause</h3>
          <p style={styles.infoCardText}>
            {incident.suspected_root_cause || 'Root cause under investigation'}
          </p>
        </div>
      </div>

      {/* Timeline */}
      <div style={styles.timelineSection}>
        <h2 style={styles.sectionTitle}>📅 Timeline</h2>
        <div style={styles.timeline}>
          {incident.timeline.map((event, index) => (
            <div key={index} style={styles.timelineItem}>
              <div style={styles.timelineDot}></div>
              <div style={styles.timelineContent}>
                <div style={styles.timelineHeader}>
                  <span style={styles.timelineType}>
                    {getEventIcon(event.event_type)} {formatEventType(event.event_type)}
                  </span>
                  <span style={styles.timelineTime}>
                    {new Date(event.event_time).toLocaleString()}
                  </span>
                </div>
                {event.details && (
                  <div style={styles.timelineDetails}>{event.details}</div>
                )}
                {event.run_id && (
                  <Link to={`/runs/${event.run_id}`} style={styles.timelineLink}>
                    View Run →
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Resolution Notes */}
      {incident.resolution_notes && (
        <div style={styles.resolutionSection}>
          <h2 style={styles.sectionTitle}>✅ Resolution</h2>
          <div style={styles.resolutionCard}>
            <div style={styles.resolutionTime}>
              Resolved at: {new Date(incident.resolved_at).toLocaleString()}
            </div>
            <div style={styles.resolutionNotes}>{incident.resolution_notes}</div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    OPEN: '#f56565',
    RESOLVED: '#48bb78',
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

function formatEventType(type) {
  return type.split('_').map(word => 
    word.charAt(0) + word.slice(1).toLowerCase()
  ).join(' ');
}

function getEventIcon(type) {
  const icons = {
    RUN_FAILED: '❌',
    INCIDENT_CREATED: '🚨',
    INCIDENT_RESOLVED: '✅',
  };
  return icons[type] || '📌';
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
    alignItems: 'flex-start',
    marginBottom: '2rem',
  },
  title: {
    fontSize: '2rem',
    fontWeight: 'bold',
    color: '#2d3748',
    marginBottom: '0.5rem',
  },
  subtitle: {
    fontSize: '1.125rem',
    color: '#4a5568',
  },
  statusBadge: {
    color: 'white',
    padding: '0.5rem 1rem',
    borderRadius: '20px',
    fontSize: '0.875rem',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  mainInfo: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '1.5rem',
    marginBottom: '2rem',
  },
  infoCard: {
    background: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  infoCardTitle: {
    fontSize: '1.125rem',
    fontWeight: '600',
    marginBottom: '0.75rem',
    color: '#2d3748',
  },
  infoCardText: {
    color: '#4a5568',
    lineHeight: '1.6',
  },
  timelineSection: {
    marginBottom: '2rem',
  },
  sectionTitle: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    marginBottom: '1rem',
    color: '#2d3748',
  },
  timeline: {
    background: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  timelineItem: {
    display: 'flex',
    position: 'relative',
    paddingLeft: '2rem',
    paddingBottom: '2rem',
    borderLeft: '2px solid #e2e8f0',
  },
  timelineDot: {
    position: 'absolute',
    left: '-6px',
    top: '4px',
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    background: '#667eea',
  },
  timelineContent: {
    flex: 1,
    marginLeft: '1rem',
  },
  timelineHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  timelineType: {
    fontWeight: '600',
    color: '#2d3748',
  },
  timelineTime: {
    fontSize: '0.875rem',
    color: '#718096',
  },
  timelineDetails: {
    color: '#4a5568',
    marginBottom: '0.5rem',
  },
  timelineLink: {
    color: '#667eea',
    textDecoration: 'none',
    fontSize: '0.875rem',
    fontWeight: '500',
  },
  resolutionSection: {
    marginBottom: '2rem',
  },
  resolutionCard: {
    background: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    borderLeft: '4px solid #48bb78',
  },
  resolutionTime: {
    fontSize: '0.875rem',
    color: '#718096',
    marginBottom: '0.75rem',
  },
  resolutionNotes: {
    color: '#2d3748',
    lineHeight: '1.6',
  },
};

