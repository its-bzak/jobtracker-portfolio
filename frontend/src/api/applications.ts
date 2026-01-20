import { api } from './client';

export type ApplicationStatus = 'DR' | 'AP' | 'RE' | 'IN' | 'OF';

export interface Application {
  id: number;
  job: number | { id: number; title: string; company: number | { id: number; name: string } };
  applicant: number | { id: number; username?: string; email?: string };
  notes?: string | null;
  application_date?: string | null;
  status: ApplicationStatus;
}

export const getApplications = async (): Promise<Application[]> => {
  const response = await api.get<Application[]>('/api/applications/');
  return response.data;
};

export const getApplication = async (id: number): Promise<Application> => {
  const response = await api.get<Application>(`/api/applications/${id}/`);
  return response.data;
};

export const updateApplication = async (id: number, data: Partial<Application>): Promise<Application> => {
  const response = await api.patch<Application>(`/api/applications/${id}/`, data);
  return response.data;
};

export const deleteApplication = async (id: number): Promise<void> => {
  await api.delete(`/api/applications/${id}/`);
};

export const submitApplication = async (id: number): Promise<{ id: number; status: ApplicationStatus }> => {
  const response = await api.post(`/api/applications/${id}/submit/`);
  return response.data;
};

export const withdrawApplication = async (id: number): Promise<{ id: number; status: ApplicationStatus }> => {
  const response = await api.post(`/api/applications/${id}/withdraw/`);
  return response.data;
};
