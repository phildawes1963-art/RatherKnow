import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import '@/App.css';
import { AuthProvider } from '@/lib/auth';
import ProtectedRoute from '@/components/ProtectedRoute';
import Landing from '@/pages/Landing';
import Promise from '@/pages/Promise';
import Methodology from '@/pages/Methodology';
import Safety from '@/pages/Safety';
import Learn from '@/pages/Learn';
import LearnArticle from '@/pages/LearnArticle';
import Faq from '@/pages/Faq';
import Samples from '@/pages/Samples';
import FlagCheck from '@/pages/FlagCheck';
import Runner from '@/pages/Runner';
import Results from '@/pages/Results';
import Mirrors from '@/pages/Mirrors';
import Archetypes from '@/pages/Archetypes';
import ArchetypeDetail from '@/pages/ArchetypeDetail';
import Auth from '@/pages/Auth';
import { ForgotPassword, ResetPassword } from '@/pages/PasswordReset';
import LegacyRedirect from '@/pages/LegacyRedirect';
import Partners from '@/pages/Partners';

function App() {
  return (
    <HelmetProvider>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/promise" element={<Promise />} />
            <Route path="/methodology" element={<Methodology />} />
            <Route path="/safety" element={<Safety />} />
            <Route path="/learn" element={<Learn />} />
            <Route path="/learn/:slug" element={<LearnArticle />} />
            <Route path="/faq" element={<Faq />} />
            <Route path="/partners" element={<Partners />} />
            <Route path="/samples" element={<Samples />} />
            <Route path="/flag-check" element={<FlagCheck />} />
            <Route path="/register" element={<Auth mode="register" />} />
            <Route path="/login" element={<Auth mode="login" />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/take/:instrument" element={<ProtectedRoute><Runner /></ProtectedRoute>} />
            <Route path="/results/:sessionId" element={<ProtectedRoute><Results /></ProtectedRoute>} />
            <Route path="/mirrors" element={<ProtectedRoute><Mirrors /></ProtectedRoute>} />
            <Route path="/archetypes" element={<Archetypes />} />            <Route path="/archetypes/:slug" element={<ArchetypeDetail />} />
            <Route path="/mirror/*" element={<LegacyRedirect />} />
            <Route path="/mirror-index/*" element={<LegacyRedirect />} />
            <Route path="*" element={<LegacyRedirect />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </HelmetProvider>
  );
}

export default App;
