import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import Layout from './components/common/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import IdeaComparison from './pages/IdeaComparison';
import ResearchWorkspace from './pages/ResearchWorkspace';
import PatentSearchPage from './pages/PatentSearchPage';
import GapAnalysisPage from './pages/GapAnalysisPage';
import RoadmapPage from './pages/RoadmapPage';
import MentorPage from './pages/MentorPage';
import ReportsPage from './pages/ReportsPage';
import PresentationPage from './pages/PresentationPage';
import SettingsPage from './pages/SettingsPage';

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 text-sm">
        <span className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mr-3" />
        Authenticating session...
      </div>
    );
  }
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="projects" element={<Projects />} />
        <Route path="projects/:id/compare" element={<IdeaComparison />} />
        <Route path="projects/:id/research" element={<ResearchWorkspace />} />
        <Route path="projects/:id/patents" element={<PatentSearchPage />} />
        <Route path="projects/:id/gaps" element={<GapAnalysisPage />} />
        <Route path="projects/:id/roadmap" element={<RoadmapPage />} />
        <Route path="projects/:id/mentor" element={<MentorPage />} />
        <Route path="mentor" element={<MentorPage />} />
        <Route path="projects/:id/reports" element={<ReportsPage />} />
        <Route path="projects/:id/presentations" element={<PresentationPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
