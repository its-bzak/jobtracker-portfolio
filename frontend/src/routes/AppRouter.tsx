import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "../pages/Login";
import JobBoard from "../pages/JobBoard";
import RequireAuth from "../auth/RequireAuth";
import Register from "../pages/Register";
import Logout from "../pages/Logout";
import Applications from "../pages/ApplicationsPage";
import Profile from "../pages/ProfilePage";
import Messages from "../pages/MessageBoard";
import AppLayout from "../layouts/AppLayout";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes> {/* Public routes */}
        <Route path="/" element={<Navigate to="/jobs" replace />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route element={<RequireAuth />}> {/* Protected routes */ }
        <Route element={<AppLayout />}>
          <Route path="/jobs" element={<JobBoard />} />
          <Route path="/logout" element={<Logout/>} />
          <Route path="/applications" element={<Applications />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/messages" element={<Messages />} />
        </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}