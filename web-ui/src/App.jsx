import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Header } from './components';
import { SessionsList } from './pages/SessionsList';
import { Step1Input } from './steps/Step1Input';
import { SessionLayout } from './layouts/SessionLayout';
import { HomeLayout } from './layouts/HomeLayout';
import { Step2Build } from './steps/Step2Build';
import { Step3Edit } from './steps/Step3Edit';
import { Step4Execute } from './steps/Step4Execute';
import { Step5Review } from './steps/Step5Review';

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <div className="flex-1 flex min-h-0">
            <Routes>
          <Route element={<HomeLayout />}>
              <Route path="/" element={<Step1Input />} />
              <Route path="/sessions" element={<SessionsList />} />
          </Route>

          <Route path="/sessions/:sessionId/*" element={<SessionLayout />}>
            <Route path="build" element={<Step2Build />} />
            <Route path="edit" element={<Step3Edit />} />
            <Route path="execute" element={<Step4Execute />} />
            <Route path="review" element={<Step5Review />} />
          </Route>
        </Routes>
      </div>
    </div>
  );
}

export default App;
