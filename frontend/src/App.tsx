import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ToastProvider } from './components/Toast';
import RTLLayout from './layouts/RTLLayout';
import ParticipantHome from './pages/ParticipantHome';
import SubmitStatement from './pages/SubmitStatement';
import VotingBooth from './pages/VotingBooth';
import MyProgress from './pages/MyProgress';
import Dashboard from './pages/Dashboard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10000,
      refetchOnWindowFocus: true,
      retry: 2,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <RTLLayout>
            <Routes>
              <Route path="/" element={<ParticipantHome />} />
              <Route path="/submit" element={<SubmitStatement />} />
              <Route path="/vote" element={<VotingBooth />} />
              <Route path="/progress" element={<MyProgress />} />
              <Route path="/dashboard" element={<Dashboard />} />
            </Routes>
          </RTLLayout>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}
