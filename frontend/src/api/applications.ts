import { api } from './client';

export type ApplicationStatus = 'DR' | 'AP' | 'RE' | 'IN' | 'OF';

export interface Application {
  id: number;
  job: number | { id: number; title: string; company: number | { id: number; name: string } };
  applicant: number | { id: number; username?: string; email?: string };
  resume?: string | null;
  cover_letter?: string | null;
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

export const createAnswer = async (applicationId: number, questionId: number, answerValue: string) => {
  const response = await api.post('/api/job-app-answers/', {
    application: applicationId,
    question: questionId,
    answer_value: answerValue,
  });
  return response.data;
};

export const updateAnswer = async (answerId: number, answerValue: string) => {
  const response = await api.patch(`/api/job-app-answers/${answerId}/`, {
    answer_value: answerValue,
  });
  return response.data;
};

export const uploadResume = async (id: number, file: File) => {
  const form = new FormData();
  form.append('resume', file);
  const response = await api.patch(`/api/applications/${id}/`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data as Application;
};

export const uploadCoverLetter = async (id: number, file: File) => {
  const form = new FormData();
  form.append('cover_letter', file);
  const response = await api.patch(`/api/applications/${id}/`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data as Application;
};
