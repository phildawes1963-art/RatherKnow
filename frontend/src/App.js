import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import '@/App.css';
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

function App() {
  return (
    <HelmetProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/promise" element={<Promise />} />
          <Route path="/methodology" element={<Methodology />} />
          <Route path="/safety" element={<Safety />} />
          <Route path="/learn" element={<Learn />} />
          <Route path="/learn/:slug" element={<LearnArticle />} />
          <Route path="/faq" element={<Faq />} />
          <Route path="/samples" element={<Samples />} />
          <Route path="/flag-check" element={<FlagCheck />} />
          <Route path="/take/:instrument" element={<Runner />} />
          <Route path="/results/:sessionId" element={<Results />} />
          <Route path="/mirrors" element={<Mirrors />} />
          <Route path="/archetypes" element={<Archetypes />} />
          <Route path="/archetypes/:slug" element={<ArchetypeDetail />} />
        </Routes>
      </BrowserRouter>
    </HelmetProvider>
  );
}

export default App;
