import { api } from './client';

export interface JobPosting {
  id: number;
  title: string;
  company: number | { id: number; name: string };
  location: string;
  employment_means: 'RE' | 'ON' | 'HY';
  employment_type: 'FT' | 'PT' | 'CT' | 'IN';
  salary_range: string | null;
  currency_code: string;
  description: string;
  posted_date: string;
}

export const getJobPostings = async (): Promise<JobPosting[]> => {
  const response = await api.get<JobPosting[]>('/api/job-postings/');
  return response.data;
};

export const getJobPosting = async (id: number): Promise<JobPosting> => {
  const response = await api.get<JobPosting>(`/api/job-postings/${id}/`);
  return response.data;
};

export const createJobPosting = async (data: Partial<JobPosting>): Promise<JobPosting> => {
  const response = await api.post<JobPosting>('/api/job-postings/', data);
  return response.data;
};

export const updateJobPosting = async (id: number, data: Partial<JobPosting>): Promise<JobPosting> => {
  const response = await api.patch<JobPosting>(`/api/job-postings/${id}/`, data);
  return response.data;
};

export const deleteJobPosting = async (id: number): Promise<void> => {
  await api.delete(`/api/job-postings/${id}/`);
};

export const applyToJob = async (jobId: number) => {
  const response = await api.post(`/api/job-postings/${jobId}/apply/`);
  return response.data;
};
