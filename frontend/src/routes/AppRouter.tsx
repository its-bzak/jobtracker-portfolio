import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Login from "../pages/Login";
import Register from "../pages/Register";
import Logout from "../pages/Logout";

import RequireRole from "../auth/RequireRole";
import AppLayout from "../layouts/AppLayout";
import RequireAuth from "../auth/RequireAuth";
// Applicant pages
import ApplicantJobs from "../pages/applicant/JobBoard";
import JobDetail from "../pages/applicant/JobDetail";
import ApplicantApplications from "../pages/applicant/ApplicationsPage";
import ApplicationEdit from "../pages/applicant/ApplicationEdit";
import ApplicantProfile from "../pages/applicant/ProfilePage";
import ApplicantMessages from "../pages/applicant/MessageBoard";
// Employer pages
import EmployerJobPostings from "../pages/employer/JobPostings";
import EmployerApplications from "../pages/employer/ApplicantsPage";
import EmployerProfile from "../pages/employer/ProfilePage";
import EmployerMessages from "../pages/employer/MessageBoard";

import RoleHomeRedirect from "../auth/RoleHomeRedirect";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* public */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* protected shell */}
        <Route element={<RequireAuth />}>
          <Route element={<AppLayout />}>
            {/* root should send you to the correct home based on role */}
            <Route path="/" element={<RoleHomeRedirect />} />

            <Route path="/logout" element={<Logout />} />

            {/* applicant group */}
            <Route element={<RequireRole role="AP" />}>
              <Route path="/applicant/jobs" element={<ApplicantJobs />} />
              <Route path="/applicant/jobs/:id" element={<JobDetail />} />
              <Route path="/applicant/applications" element={<ApplicantApplications />} />
              <Route path="/applicant/applications/:id/edit" element={<ApplicationEdit />} />
              <Route path="/applicant/messages" element={<ApplicantMessages />} />
              <Route path="/applicant/profile" element={<ApplicantProfile />} />
            </Route>

            {/* employer group */}
            <Route element={<RequireRole role="EM" />}>
              <Route path="/employer/jobs" element={<EmployerJobPostings />} />
              <Route path="/employer/applications" element={<EmployerApplications />} />
              <Route path="/employer/messages" element={<EmployerMessages />} />
              <Route path="/employer/profile" element={<EmployerProfile />} />
            </Route>

            {/* catch-all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}