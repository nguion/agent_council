import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { Header, UserSessionsSidebar } from './components';
import { SessionsList } from './pages/SessionsList';
import { Step1Input } from './steps/Step1Input';
import { SessionLayout } from './layouts/SessionLayout';
import { Step2Build } from './steps/Step2Build';
import { Step3Edit } from './steps/Step3Edit';
import { Step4Execute } from './steps/Step4Execute';
import { Step5Review } from './steps/Step5Review';

function App() {
  const location = useLocation();
  const isSessionRoute = location.pathname.startsWith('/sessions/') && location.pathname.split('/').length > 3;

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      {/* For non-session routes, show UserSessionsSidebar separately */}
      {!isSessionRoute ? (
        <div className="flex-1 flex">
          <UserSessionsSidebar />
          <main className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/" element={<Step1Input />} />
              <Route path="/sessions" element={<SessionsList />} />
            </Routes>
          </main>
        </div>
      ) : (
        <Routes>
          {/* Session Routes with Layout (includes UserSessionsSidebar) */}
          <Route path="/sessions/:sessionId/*" element={<SessionLayout />}>
            <Route path="build" element={<Step2Build />} />
            <Route path="edit" element={<Step3Edit />} />
            <Route path="execute" element={<Step4Execute />} />
            <Route path="review" element={<Step5Review />} />
          </Route>
        </Routes>
      )}
    </div>
  );
}

export default App;
