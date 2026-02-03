import { useEffect, useState, useCallback } from 'react';
import { getApplications, promoteToInterview, offerApplication, rejectApplication } from '../../api/applications';
import { getJobPostings } from '../../api/jobs';
import type { Application } from '../../api/applications';
import type { JobPosting } from '../../api/jobs';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import styles from './ApplicantsPage.module.css';

const statusLabel: Record<string, string> = {
  DR: 'Draft',
  AP: 'Applied',
  RE: 'Rejected',
  IN: 'Interview',
  OF: 'Offered',
};

const statusColor: Record<string, string> = {
  DR: 'draft',
  AP: 'applied',
  RE: 'rejected',
  IN: 'interview',
  OF: 'offered',
};

export default function EmployerApplications() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [jobs, setJobs] = useState<JobPosting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [filterJob, setFilterJob] = useState<number | null>(null);
  const [filterStatus, setFilterStatus] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [apps, jobPostings] = await Promise.all([getApplications(), getJobPostings()]);
      setApplications(apps);
      setJobs(jobPostings);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
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

  const getApplicantName = (app: Application) => {
    if (typeof app.applicant === 'object') return app.applicant.username || `Applicant #${app.applicant.id}`;
    return `Applicant #${app.applicant}`;
  };

  const handlePromoteToInterview = async (id: number) => {
    try {
      setActionLoading(id);
      await promoteToInterview(id);
      alert('Application moved to Interview stage');
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update application');
    } finally {
      setActionLoading(null);
    }
  };

  const handleOffer = async (id: number) => {
    try {
      setActionLoading(id);
      await offerApplication(id);
      alert('Offer sent to applicant');
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to send offer');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (id: number) => {
    if (!confirm('Are you sure you want to reject this application?')) return;

    try {
      setActionLoading(id);
      await rejectApplication(id);
      alert('Application rejected');
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to reject application');
    } finally {
      setActionLoading(null);
    }
  };

  const filteredApplications = applications.filter(app => {
    if (filterJob && (typeof app.job === 'number' ? app.job : app.job.id) !== filterJob) return false;
    if (filterStatus && app.status !== filterStatus) return false;
    return true;
  });

  if (loading) {
    return <div className={styles.container}>Loading applications...</div>;
  }

  if (error) {
    return <div className={styles.container}>Error: {error}</div>;
  }

  return (
    <div className={styles.container}>
      <h1>Incoming Applications</h1>

      {applications.length === 0 ? (
        <Card>
          <p className={styles.emptyState}>No applications yet. Once applicants apply to your jobs, they will appear here.</p>
        </Card>
      ) : (
        <>
          <div className={styles.filters}>
            <div className={styles.filterGroup}>
              <label htmlFor="filterJob">Filter by Job</label>
              <select
                id="filterJob"
                value={filterJob || ''}
                onChange={(e) => setFilterJob(e.target.value ? parseInt(e.target.value) : null)}
              >
                <option value="">All Jobs</option>
                {jobs.map(job => (
                  <option key={job.id} value={job.id}>{job.title}</option>
                ))}
              </select>
            </div>

            <div className={styles.filterGroup}>
              <label htmlFor="filterStatus">Filter by Status</label>
              <select
                id="filterStatus"
                value={filterStatus || ''}
                onChange={(e) => setFilterStatus(e.target.value || null)}
              >
                <option value="">All Statuses</option>
                <option value="AP">Applied</option>
                <option value="IN">Interview</option>
                <option value="OF">Offered</option>
                <option value="RE">Rejected</option>
              </select>
            </div>
          </div>

          {filteredApplications.length === 0 ? (
            <Card>
              <p className={styles.emptyState}>No applications match your filters.</p>
            </Card>
          ) : (
            <div className={styles.applicationsGrid}>
              {filteredApplications.map((app) => {
                const job = getJobForApplication(app);
                const applicantName = getApplicantName(app);

                return (
                  <Card key={app.id} className={styles.applicationCard}>
                    <div className={styles.header}>
                      <div className={styles.applicantInfo}>
                        <h2 className={styles.applicantName}>{applicantName}</h2>
                        <p className={styles.jobTitle}>
                          {job ? job.title : `Job #${typeof app.job === 'number' ? app.job : app.job.id}`}
                        </p>
                      </div>
                      <div className={`${styles.statusBadge} ${styles[`status-${statusColor[app.status]}` as keyof typeof styles]}`}>
                        {statusLabel[app.status]}
                      </div>
                    </div>

                    <div className={styles.details}>
                      <div className={styles.detailRow}>
                        <span className={styles.label}>Date Received:</span>
                        <span className={styles.applicationDate}>{formatDate(app.application_date)}</span>
                      </div>
                      {app.notes && (
                        <div className={styles.detailRow}>
                          <span className={styles.label}>Note:</span>
                          <span className={styles.notes}>{app.notes}</span>
                        </div>
                      )}
                    </div>

                    <div className={styles.actions}>
                      {app.status === 'AP' && (
                        <>
                          <Button
                            variant="primary"
                            onClick={() => handlePromoteToInterview(app.id)}
                            disabled={actionLoading === app.id}
                            size="sm"
                          >
                            Move to Interview
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => handleOffer(app.id)}
                            disabled={actionLoading === app.id}
                            size="sm"
                          >
                            Send Offer
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => handleReject(app.id)}
                            disabled={actionLoading === app.id}
                            size="sm"
                          >
                            Reject
                          </Button>
                        </>
                      )}

                      {app.status === 'IN' && (
                        <>
                          <Button
                            variant="primary"
                            onClick={() => handleOffer(app.id)}
                            disabled={actionLoading === app.id}
                            size="sm"
                          >
                            Send Offer
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => handleReject(app.id)}
                            disabled={actionLoading === app.id}
                            size="sm"
                          >
                            Reject
                          </Button>
                        </>
                      )}

                      {(app.status === 'OF' || app.status === 'RE') && (
                        <div className={styles.noActions}>No actions available</div>
                      )}
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}