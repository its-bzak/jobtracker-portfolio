import { useEffect, useState, useCallback } from 'react';
import { getJobPostings, createJobPosting, updateJobPosting, deleteJobPosting } from '../../api/jobs';
import type { JobPosting } from '../../api/jobs';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { formatSalary } from '../../utils/salary';
import styles from './JobPostings.module.css';

export default function EmployerJobPostings() {
  const [jobs, setJobs] = useState<JobPosting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    location: '',
    employment_means: 'ON' as 'RE' | 'ON' | 'HY',
    employment_type: 'FT' as 'FT' | 'PT' | 'CT' | 'IN',
    salary_range: '',
    currency_code: 'USD',
    description: '',
  });
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitLoading, setSubmitLoading] = useState(false);

  const fetchJobs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getJobPostings();
      setJobs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load job postings');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitError(null);
    setSubmitLoading(true);

    try {
      await createJobPosting(formData);
      setFormData({
        title: '',
        location: '',
        employment_means: 'ON',
        employment_type: 'FT',
        salary_range: '',
        currency_code: 'USD',
        description: '',
      });
      setShowForm(false);
      alert('Job posting created successfully!');
      fetchJobs();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create job posting';
      setSubmitError(errorMessage);
      console.error(err);
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleDelete = async (jobId: number) => {
    if (!confirm('Are you sure you want to delete this job posting? This will not affect existing applications.')) return;

    try {
      await deleteJobPosting(jobId);
      alert('Job posting deleted successfully');
      fetchJobs();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete job posting');
    }
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
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

  if (loading) {
    return <div className={styles.container}>Loading job postings...</div>;
  }

  if (error) {
    return <div className={styles.container}>Error: {error}</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Job Postings</h1>
        <Button
          variant="primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancel' : '+ Create Job'}
        </Button>
      </div>

      {showForm && (
        <Card className={styles.formCard}>
          <h2>Create New Job Posting</h2>
          {submitError && <div className={styles.error}>{submitError}</div>}
          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.formGroup}>
              <label htmlFor="title">Job Title *</label>
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                required
                placeholder="e.g., Senior Software Engineer"
              />
            </div>

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label htmlFor="location">Location *</label>
                <input
                  type="text"
                  id="location"
                  name="location"
                  value={formData.location}
                  onChange={handleInputChange}
                  required
                  placeholder="e.g., San Francisco, CA"
                />
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="salary_range">Salary Range</label>
                <input
                  type="text"
                  id="salary_range"
                  name="salary_range"
                  value={formData.salary_range}
                  onChange={handleInputChange}
                  placeholder="e.g., 120,000 - 160,000"
                />
              </div>
            </div>

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label htmlFor="currency_code">Currency *</label>
                <select
                  id="currency_code"
                  name="currency_code"
                  value={formData.currency_code}
                  onChange={handleInputChange}
                  required
                >
                  <option value="USD">US Dollar (USD)</option>
                  <option value="EUR">Euro (EUR)</option>
                  <option value="GBP">British Pound (GBP)</option>
                  <option value="CAD">Canadian Dollar (CAD)</option>
                  <option value="AUD">Australian Dollar (AUD)</option>
                  <option value="JPY">Japanese Yen (JPY)</option>
                  <option value="CHF">Swiss Franc (CHF)</option>
                  <option value="CNY">Chinese Yuan (CNY)</option>
                  <option value="INR">Indian Rupee (INR)</option>
                  <option value="MXN">Mexican Peso (MXN)</option>
                </select>
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="employment_type">Employment Type *</label>
                <select
                  id="employment_type"
                  name="employment_type"
                  value={formData.employment_type}
                  onChange={handleInputChange}
                  required
                >
                  <option value="FT">Full-time</option>
                  <option value="PT">Part-time</option>
                  <option value="CT">Contract</option>
                  <option value="IN">Internship</option>
                </select>
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="employment_means">Work Location *</label>
                <select
                  id="employment_means"
                  name="employment_means"
                  value={formData.employment_means}
                  onChange={handleInputChange}
                  required
                >
                  <option value="ON">On-site</option>
                  <option value="RE">Remote</option>
                  <option value="HY">Hybrid</option>
                </select>
              </div>
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="description">Job Description *</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                required
                placeholder="Enter the full job description, responsibilities, and requirements..."
                rows={6}
              />
            </div>

            <div className={styles.formActions}>
              <Button type="submit" variant="primary" disabled={submitLoading}>
                {submitLoading ? 'Creating...' : 'Create Job Posting'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowForm(false)}
                disabled={submitLoading}
              >
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      )}

      <div className={styles.jobsContainer}>
        {jobs.length === 0 ? (
          <p className={styles.emptyState}>
            {showForm ? 'Create your first job posting to get started!' : 'No job postings yet. Click "Create Job" to post a position.'}
          </p>
        ) : (
          <div className={styles.jobGrid}>
            {jobs.map((job) => (
              <Card key={job.id} className={styles.jobCard}>
                <div className={styles.jobHeader}>
                  <div className={styles.titleSection}>
                    <h2 className={styles.jobTitle}>{job.title}</h2>
                    <Badge type={getEmploymentTypeBadge(job.employment_type)} />
                  </div>
                </div>

                <div className={styles.jobInfo}>
                  <p className={styles.location}>{job.location}</p>
                  {job.salary_range && (
                    <p className={styles.salary}>
                      <strong>Salary:</strong> {formatSalary(job.salary_range, job.currency_code)}
                    </p>
                  )}
                </div>

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
                  <Button
                    variant="outline"
                    onClick={() => handleDelete(job.id)}
                  >
                    Delete
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}