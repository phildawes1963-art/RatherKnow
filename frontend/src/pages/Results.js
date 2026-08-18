import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Shell from '../components/Shell';
import FindingsTeaser from '../components/FindingsTeaser';
import SituationLens from '../components/SituationLens';
import DownloadReport from '../components/DownloadReport';
import { API } from '../lib/mirrorTheme';
import { authHeaders } from '../lib/auth';
import ClosenessResult from './results/ClosenessResult';
import EssentialResult from './results/EssentialResult';
import PersonalityResult from './results/PersonalityResult';
import EqResult from './results/EqResult';

const VIEWS = {
  'MI-AS-36': ClosenessResult,
  essential: EssentialResult,
  personality: PersonalityResult,
  eq: EqResult,
};

const TITLES = {
  'MI-AS-36': 'Closeness Mirror — your result',
  essential: 'Essential Mirror — your result',
  personality: 'Personality Mirror — your result',
  eq: 'EI Mirror — your result',
};

export default function Results() {
  const { sessionId } = useParams();
  const [result, setResult] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/api/v2/assessments/${sessionId}/result`, { headers: authHeaders() });
        if (!res.ok) throw new Error();
        setResult(await res.json());
      } catch {
        setError(true);
      }
    })();
  }, [sessionId]);

  if (error) {
    return (
      <Shell title="Result not found">
        <div className="max-w-2xl mx-auto px-5 py-24" data-testid="results-error">
          <p className="text-[#3B3B34]">We couldn’t find that result. It may not be complete yet.</p>
          <Link className="underline underline-offset-4 mt-4 inline-block" to="/">Back to Rather Know</Link>
        </div>
      </Shell>
    );
  }

  if (!result) {
    return (
      <Shell title="Your result">
        <div className="max-w-2xl mx-auto px-5 py-24 text-[#6E6E66]" data-testid="results-loading">Reading your result…</div>
      </Shell>
    );
  }

  const View = VIEWS[result.instrument];
  const currentKey = result.instrument === 'MI-AS-36' ? 'closeness' : result.instrument;
  return (
    <Shell title={TITLES[result.instrument] || 'Your result'}>
      <div className="max-w-3xl mx-auto px-5 sm:px-8 py-14 sm:py-20" data-testid="results-page">
        <View result={result} />
        <SituationLens instrument={result.instrument} />
        <div className="mt-12">
          <DownloadReport sessionId={sessionId} instrumentName={TITLES[result.instrument]?.split(' —')[0] || 'report'} />
        </div>
        <FindingsTeaser current={currentKey} />
      </div>
    </Shell>
  );
}
