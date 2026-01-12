import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getApplication, updateApplication, uploadResume, uploadCoverLetter, updateAnswer, createAnswer } from '../../api/applications';
import { applyToJob } from '../../api/jobs';
import type { Application } from '../../api/applications';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import styles from './ApplicationEdit.module.css';

type QuestionPayload = {
  question: {
    id: number;
    question_prompt: string;
    answer_type: string;
    required: boolean;
  };
  answer: {
    id: number;
    application: number;
    question: number;
    answer_value: string | null;
  } | null;
};

export default function ApplicationEdit() {
  const { id } = useParams();
  const appId = Number(id);
  const navigate = useNavigate();

  const [application, setApplication] = useState<Application | null>(null);
  const [questions, setQuestions] = useState<QuestionPayload[]>([]);
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
        // request job apply payload to get questions + answers (backend creates answers if missing)
        const jobId = typeof app.job === 'number' ? app.job : app.job.id;
        const resp = await applyToJob(jobId);
        setQuestions(resp.questions ?? []);
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

  const handleResume = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!application) return;
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await uploadResume(application.id, file);
      alert('Resume uploaded.');
      const refreshed = await getApplication(application.id);
      setApplication(refreshed);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to upload resume.');
    }
  };

  const handleCoverLetter = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!application) return;
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await uploadCoverLetter(application.id, file);
      alert('Cover letter uploaded.');
      const refreshed = await getApplication(application.id);
      setApplication(refreshed);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to upload cover letter.');
    }
  };

  const handleAnswerChange = (index: number, value: string) => {
    const copy = [...questions];
    copy[index] = { ...copy[index], answer: { ...(copy[index].answer ?? { id: -1, application: application?.id ?? -1, question: copy[index].question.id, answer_value: '' }), answer_value: value } };
    setQuestions(copy);
  };

  const saveAnswer = async (q: QuestionPayload) => {
    if (!application) return;
    const answerVal = q.answer?.answer_value ?? '';
    try {
      if (q.answer && q.answer.id && q.answer.id > 0) {
        await updateAnswer(q.answer.id, answerVal);
      } else {
        await createAnswer(application.id, q.question.id, answerVal);
      }
      alert('Saved.');
      // refresh answers
      const jobId = typeof application.job === 'number' ? application.job : application.job.id;
      const resp = await applyToJob(jobId);
      setQuestions(resp.questions ?? []);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to save answer.');
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
          <label className={styles.label}>Resume</label>
          {application.resume ? (
            <div className={styles.fileRow}>
              <a href={application.resume} target="_blank" rel="noreferrer">View resume</a>
            </div>
          ) : (
            <div className={styles.fileRow}>No resume uploaded.</div>
          )}
          <input type="file" accept=".pdf,.doc,.docx" onChange={handleResume} />
        </div>

        <div className={styles.section}>
          <label className={styles.label}>Cover letter</label>
          {application.cover_letter ? (
            <div className={styles.fileRow}><a href={application.cover_letter} target="_blank" rel="noreferrer">View cover letter</a></div>
          ) : (
            <div className={styles.fileRow}>No cover letter uploaded.</div>
          )}
          <input type="file" accept=".pdf,.doc,.docx" onChange={handleCoverLetter} />
        </div>

        <div className={styles.section}>
          <label className={styles.label}>Notes</label>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} className={styles.textarea} />
          <div style={{ marginTop: 8 }}>
            <Button variant="outline" onClick={onSaveNotes}>Save Notes</Button>
          </div>
        </div>

        <div className={styles.section}>
          <label className={styles.label}>Application Questions</label>
          {questions.length === 0 ? (
            <p>No questions for this job.</p>
          ) : (
            questions.map((q, idx) => (
              <div key={q.question.id} className={styles.questionRow}>
                <div className={styles.prompt}>{q.question.question_prompt}{q.question.required ? ' *' : ''}</div>
                <div className={styles.answerControls}>
                  {q.question.answer_type === 'Short Answer' && (
                    <input className={styles.input} value={q.answer?.answer_value ?? ''} onChange={(e) => handleAnswerChange(idx, e.target.value)} />
                  )}
                  {q.question.answer_type === 'Long Answer' && (
                    <textarea className={styles.textarea} value={q.answer?.answer_value ?? ''} onChange={(e) => handleAnswerChange(idx, e.target.value)} />
                  )}
                  {q.question.answer_type === 'Number' && (
                    <input type="number" className={styles.input} value={q.answer?.answer_value ?? ''} onChange={(e) => handleAnswerChange(idx, e.target.value)} />
                  )}
                  {q.question.answer_type === 'Date' && (
                    <input type="date" className={styles.input} value={q.answer?.answer_value ?? ''} onChange={(e) => handleAnswerChange(idx, e.target.value)} />
                  )}
                  {q.question.answer_type === 'Yes/No' && (
                    <select className={styles.input} value={q.answer?.answer_value ?? ''} onChange={(e) => handleAnswerChange(idx, e.target.value)}>
                      <option value="">--</option>
                      <option value="Yes">Yes</option>
                      <option value="No">No</option>
                    </select>
                  )}

                  <div>
                    <Button variant="outline" onClick={() => saveAnswer(q)}>Save</Button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        <div className={styles.actions}>
          <Button variant="primary" onClick={handleSubmitApp}>Submit Application</Button>
          <Button variant="outline" onClick={() => navigate('/applicant/applications')}>Back to Applications</Button>
        </div>
      </Card>
    </div>
  );
}
