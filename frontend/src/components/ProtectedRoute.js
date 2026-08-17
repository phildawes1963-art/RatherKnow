import { Navigate, useLocation } from 'react-router-dom';
import Shell from './Shell';
import { useAuth } from '../lib/auth';

export default function ProtectedRoute({ children }) {
  const { user } = useAuth();
  const { pathname } = useLocation();

  if (user === null) {
    return (
      <Shell title="One moment">
        <div className="max-w-2xl mx-auto px-5 py-24 text-[#6E6E66]" data-testid="auth-checking">Checking your session…</div>
      </Shell>
    );
  }
  if (!user) return <Navigate to={`/register?next=${encodeURIComponent(pathname)}`} replace />;
  return children;
}
