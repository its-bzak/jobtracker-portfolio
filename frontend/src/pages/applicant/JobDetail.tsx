import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getJobPosting, applyToJob } from '../../api/jobs';
import type { JobPosting } from '../../api/jobs';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import styles from './JobDetail.module.css';

export default function JobDetail() {
  const { id } = useParams();
  const jobId = Number(id);
  const navigate = useNavigate();

  const [job, setJob] = useState<JobPosting | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await getJobPosting(jobId);
        setJob(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load job posting');
      } finally {
        setLoading(false);
      }
    };

    if (!Number.isNaN(jobId)) fetch();
  }, [jobId]);

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return dateString;
    }
  };

  const handleApply = async () => {
    if (!job) return;
    try {
      const resp: any = await applyToJob(jobId);
      alert('Application created.');
      const appId = resp?.application?.id ?? resp?.application_id ?? resp?.id;
      if (appId) navigate(`/applicant/applications/${appId}/edit`);
    } catch (err: any) {
      if (err?.response?.data?.detail) alert(err.response.data.detail);
      else alert(err instanceof Error ? err.message : 'Failed to apply');
    }
  };

  if (loading) return <div className={styles.container}>Loading job...</div>;
  if (error) return <div className={styles.container}>Error: {error}</div>;
  if (!job) return <div className={styles.container}>Job not found.</div>;

  return (
    <div className={styles.container}>
      <h1>Job Details</h1>
      <Card className={styles.card}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.title}>{job.title}</h2>
            <p className={styles.company}>{typeof job.company === 'object' ? job.company.name : `Company #${job.company}`}</p>
          </div>
          <div>
            <Badge type={job.employment_type === 'FT' ? 'full-time' : job.employment_type === 'PT' ? 'part-time' : job.employment_type === 'IN' ? 'internship' : 'contract'} />
          </div>
        </div>

        <div className={styles.meta}>
          <div><strong>Location:</strong> {job.location}</div>
          <div><strong>Posted:</strong> {formatDate(job.posted_date)}</div>
          <div><strong>Employment:</strong> {job.employment_means === 'RE' ? 'Remote' : job.employment_means === 'ON' ? 'On-site' : 'Hybrid'}</div>
          {job.salary_range && <div><strong>Salary:</strong> {job.salary_range}</div>}
        </div>

        <div className={styles.description}>
          <h3>Description</h3>
          <p>{job.description}</p>
        </div>

        <div className={styles.actions}>
          <Button variant="primary" onClick={handleApply}>Apply</Button>
          <Button variant="outline" onClick={() => navigate('/applicant/jobs')}>Back to Jobs</Button>
        </div>
      </Card>
    </div>
  );
}
