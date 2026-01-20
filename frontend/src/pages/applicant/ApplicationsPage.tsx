import { useEffect, useState, useCallback } from 'react';
import { getJobPostings } from '../../api/jobs';
import type { JobPosting } from '../../api/jobs';
import type { Application } from '../../api/applications';
import { getApplications, submitApplication, withdrawApplication, deleteApplication } from '../../api/applications';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import styles from './ApplicationsPage.module.css';
import { useNavigate } from 'react-router-dom';

const statusLabel: Record<string, string> = {
  DR: 'Draft',
  AP: 'Applied',
  RE: 'Rejected',
  IN: 'Interview',
  OF: 'Offered',
};

export default function ApplicantApplications() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [jobs, setJobs] = useState<JobPosting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [apps, jobPostings] = await Promise.all([getApplications(), getJobPostings()]);
      setApplications(apps);
      setJobs(jobPostings);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load applications');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return '—';
    try {
      return new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return dateString;
    }
  };

  const getJobForApplication = (app: Application) => {
    if (typeof app.job === 'object') return app.job;
    return jobs.find((j) => j.id === app.job);
  };

  const handleSubmit = async (id: number) => {
    try {
      await submitApplication(id);
      alert('Application submitted.');
      fetchData();
    } catch (err: any) {
      if (err?.response?.data) {
        const data = err.response.data;
        if (data.missing_questions) {
          alert('Missing required questions.');
        } else if (data.detail) {
          alert(data.detail);
        } else {
          alert('Failed to submit application.');
        }
      } else {
        alert(err instanceof Error ? err.message : 'Failed to submit application.');
      }
    }
  };

  const handleWithdraw = async (id: number) => {
    if (!confirm('Are you sure you want to withdraw this application?')) return;
    try {
      await withdrawApplication(id);
      alert('Application withdrawn.');
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to withdraw application.');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this draft application? This cannot be undone.')) return;
    try {
      await deleteApplication(id);
      alert('Application deleted.');
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete application.');
    }
  };

  const handleEdit = (app: Application) => {
    navigate(`/applicant/applications/${app.id}/edit`);
  };

  if (loading) return <div className={styles.container}>Loading applications...</div>;
  if (error) return <div className={styles.container}>Error: {error}</div>;

  return (
    <div className={styles.container}>
      <h1>Applications</h1>

      {applications.length === 0 ? (
        <p>No applications yet.</p>
      ) : (
        <div className={styles.applicationsGrid}>
          {applications.map((app) => {
            const job = getJobForApplication(app);
            return (
              <Card key={app.id} className={styles.applicationCard}>
                <div className={styles.row}>
                  <div>
                    <h2 className={styles.jobTitle}>{job ? job.title : `Job #${typeof app.job === 'number' ? app.job : app.job.id}`}</h2>
                    <p className={styles.companyName}>{job && typeof job.company === 'object' ? job.company.name : job && typeof job.company === 'number' ? `Company #${job.company}` : ''}</p>
                  </div>
                  <div className={styles.meta}>
                    <div className={`${styles.statusBadge} ${styles[`status-${app.status.toLowerCase()}`]}`}>{statusLabel[app.status] ?? app.status}</div>
                    <div className={styles.metaInfo}>ID: {app.id}</div>
                    <div className={styles.metaInfo}>Applied: {formatDate(app.application_date)}</div>
                  </div>
                </div>

                <div className={styles.actions}>
                  {app.status === 'DR' && (
                    <>
                      <Button variant="outline" onClick={() => handleEdit(app)}>Edit</Button>
                      <Button variant="primary" onClick={() => handleSubmit(app.id)}>Submit</Button>
                      <Button variant="outline" onClick={() => handleDelete(app.id)}>Delete</Button>
                    </>
                  )}

                  {app.status === 'AP' && (
                    <>
                      <Button variant="outline" onClick={() => handleWithdraw(app.id)}>Withdraw</Button>
                    </>
                  )}

                  {app.status !== 'DR' && app.status !== 'AP' && (
                    <div className={styles.noActions}>No actions available</div>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}