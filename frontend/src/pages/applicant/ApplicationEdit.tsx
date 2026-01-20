import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getApplication, updateApplication } from '../../api/applications';
import type { Application } from '../../api/applications';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import styles from './ApplicationEdit.module.css';

export default function ApplicationEdit() {
  const { id } = useParams();
  const appId = Number(id);
  const navigate = useNavigate();

  const [application, setApplication] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState<string | undefined>('');

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const app = await getApplication(appId);
        setApplication(app);
        setNotes(app.notes ?? '');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load application');
      } finally {
        setLoading(false);
      }
    };
    if (!Number.isNaN(appId)) fetch();
  }, [appId]);

  const onSaveNotes = async () => {
    if (!application) return;
    try {
      await updateApplication(application.id, { notes });
      alert('Notes saved.');
      const refreshed = await getApplication(application.id);
      setApplication(refreshed);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to save notes.');
    }
  };

  const handleSubmitApp = async () => {
    if (!application) return;
    // submit latest state
    try {
      await fetch('/api/applications/' + application.id + '/submit/', { method: 'POST', headers: { 'Content-Type': 'application/json' } });
      alert('Application submitted.');
      navigate('/applicant/applications');
    } catch (err) {
      // Let fetch fallback to alert
      alert('Failed to submit.');
    }
  };

  if (loading) return <div className={styles.container}>Loading…</div>;
  if (error) return <div className={styles.container}>Error: {error}</div>;
  if (!application) return <div className={styles.container}>Application not found.</div>;

  const jobTitle = typeof application.job === 'object' ? application.job.title : '';
  const companyName = typeof application.job === 'object' && typeof application.job.company === 'object' ? application.job.company.name : '';

  return (
    <div className={styles.container}>
      <h1>Edit Application</h1>
      <Card className={styles.card}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.jobTitle}>{jobTitle || `Job #${typeof application.job === 'number' ? application.job : (application.job as any)?.id}`}</h2>
            <p className={styles.company}>{companyName}</p>
          </div>
          <div className={styles.status}>Status: <strong>{application.status}</strong></div>
        </div>

        <div className={styles.section}>
          <label className={styles.label}>Notes</label>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} className={styles.textarea} />
          <div style={{ marginTop: 8 }}>
            <Button variant="outline" onClick={onSaveNotes}>Save Notes</Button>
          </div>
        </div>

        <div className={styles.actions}>
          <Button variant="primary" onClick={handleSubmitApp}>Submit Application</Button>
          <Button variant="outline" onClick={() => navigate('/applicant/applications')}>Back to Applications</Button>
        </div>
      </Card>
    </div>
  );
}
