import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getJobPostings, applyToJob } from '../../api/jobs';
import type { JobPosting } from "../../api/jobs";
import { useAuth } from '../../auth/AuthContext';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { formatSalary } from '../../utils/salary';
import styles from './JobBoard.module.css';

export default function JobBoard() {
  const [jobs, setJobs] = useState<JobPosting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { markNewApplicationDraft } = useAuth();

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        setLoading(true);
        const data = await getJobPostings();
        setJobs(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load job postings');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();
  }, []);

  const handleApply = async (jobId: number) => {
    try {
      await applyToJob(jobId);
      // mark that a new draft exists so the nav can show a notification dot
      markNewApplicationDraft?.(true);
      alert('Application draft created! View it in the applications page.');
    } catch (err) {
      const e: any = err;
      if (e?.response?.status === 409) {
        alert("You've already applied to this job");
        return;
      }
      if (e?.response?.data?.detail) {
        alert(e.response.data.detail);
      } else {
        alert(err instanceof Error ? err.message : 'Failed to apply to job');
      }
    }
  };

  const getEmploymentTypeBadge = (type: string): 'full-time' | 'part-time' | 'internship' | 'contract' | 'temporary' => {
    switch (type) {
      case 'FT':
        return 'full-time';
      case 'PT':
        return 'part-time';
      case 'IN':
        return 'internship';
      case 'CT':
        return 'contract';
      default:
        return 'full-time';
    }
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (loading) {
    return <div className={styles.container}>Loading job postings...</div>;
  }

  if (error) {
    return <div className={styles.container}>Error: {error}</div>;
  }

  if (jobs.length === 0) {
    return <div className={styles.container}>No job postings available.</div>;
  }

  return (
    <div className={styles.container}>
      <h1>Job Postings</h1>
      <div className={styles.jobGrid}>
        {jobs.map((job) => (
          <Card key={job.id} className={styles.jobCard}>
            <div className={styles.header}>
              <div className={styles.titleSection}>
                <h2 className={styles.jobTitle}>{job.title}</h2>
                <Badge type={getEmploymentTypeBadge(job.employment_type)} />
              </div>
            </div>

            <div className={styles.companyInfo}>
              <p className={styles.company}>
                {typeof job.company === 'object' ? job.company.name : `Company ID: ${job.company}`}
              </p>
              <p className={styles.location}>{job.location}</p>
            </div>

            {job.salary_range && (
              <p className={styles.salary}>
                <strong>Salary:</strong> {formatSalary(job.salary_range, job.currency_code)}
              </p>
            )}

            <p className={styles.description}>{job.description}</p>

            <div className={styles.metadata}>
              <span className={styles.postedDate}>Posted: {formatDate(job.posted_date)}</span>
              <span className={styles.employmentMeans}>
                {job.employment_means === 'RE'
                  ? 'Remote'
                  : job.employment_means === 'ON'
                    ? 'On-site'
                    : 'Hybrid'}
              </span>
            </div>

            <div className={styles.actions}>
              <Button variant="primary" onClick={() => handleApply(job.id)}>
                Apply
              </Button>
              <Button variant="outline" onClick={() => navigate(`/applicant/jobs/${job.id}`)}>
                View Details
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}