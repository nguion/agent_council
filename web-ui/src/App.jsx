import React, { useState, useEffect } from 'react';
import { Header, Stepper, SessionSidebar } from './components';
import { Step1Input } from './steps/Step1Input';
import { Step2Build } from './steps/Step2Build';
import { Step3Edit } from './steps/Step3Edit';
import { Step4Execute } from './steps/Step4Execute';
import { Step5Review } from './steps/Step5Review';
import { agentCouncilAPI } from './api';

function App() {
  const [currentStep, setCurrentStep] = useState('input');
  const [sessionId, setSessionId] = useState(null);
  const [sessionData, setSessionData] = useState(null);
  const [councilConfig, setCouncilConfig] = useState(null);
  const [tokens, setTokens] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Poll for session updates to keep tokens/cost up to date
  useEffect(() => {
    if (!sessionId) return;
    
    const pollSession = async () => {
      try {
        const summary = await agentCouncilAPI.getSummary(sessionId);
        setSessionData(summary);
        if (summary.tokens) {
          setTokens(summary.tokens);
        }
      } catch (err) {
        console.error('Failed to poll session:', err);
      }
    };
    
    // Poll every 5 seconds
    const interval = setInterval(pollSession, 5000);
    
    // Initial poll
    pollSession();
    
    return () => clearInterval(interval);
  }, [sessionId]);
  
  const handleStep1Next = async ({ question, files }) => {
    try {
      setLoading(true);
      const result = await agentCouncilAPI.createSession(question, files);
      setSessionId(result.session_id);
      setSessionData({ question, context_files: result.context_files });
      setCurrentStep('build');
    } catch (err) {
      alert('Failed to create session: ' + err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const handleStep2Next = (config, skipEdit) => {
    setCouncilConfig(config);
    if (skipEdit) {
      // Update council config on server
      agentCouncilAPI.updateCouncil(sessionId, config);
      setCurrentStep('execute');
    } else {
      setCurrentStep('edit');
    }
  };
  
  const handleStep3Next = async (config) => {
    try {
      setLoading(true);
      await agentCouncilAPI.updateCouncil(sessionId, config);
      setCouncilConfig(config);
      setCurrentStep('execute');
    } catch (err) {
      alert('Failed to update council: ' + err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const handleStep4Next = () => {
    setCurrentStep('review');
  };
  
  const renderStep = () => {
    switch (currentStep) {
      case 'input':
        return <Step1Input onNext={handleStep1Next} />;
      
      case 'build':
        return (
          <Step2Build
            sessionId={sessionId}
            onNext={handleStep2Next}
            onBack={() => {
              setSessionId(null);
              setSessionData(null);
              setCurrentStep('input');
            }}
          />
        );
      
      case 'edit':
        return (
          <Step3Edit
            initialConfig={councilConfig}
            onNext={handleStep3Next}
            onBack={() => setCurrentStep('build')}
          />
        );
      
      case 'execute':
        return (
          <Step4Execute
            sessionId={sessionId}
            onNext={handleStep4Next}
            onBack={() => setCurrentStep('edit')}
          />
        );
      
      case 'review':
        return (
          <Step5Review
            sessionId={sessionId}
            onBack={() => setCurrentStep('execute')}
          />
        );
      
      default:
        return <Step1Input onNext={handleStep1Next} />;
    }
  };
  
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <Stepper currentStep={currentStep} />
      
      <div className="flex-1 flex">
        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          {renderStep()}
        </main>
        
        {/* Sidebar - only show if session exists */}
        {sessionId && sessionData && (
          <SessionSidebar session={sessionData} tokens={tokens} />
        )}
      </div>
      
      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-25 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 shadow-xl">
            <div className="animate-spin h-8 w-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto"></div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
