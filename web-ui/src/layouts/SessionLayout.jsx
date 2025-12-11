import React, { useState, useEffect, useRef } from 'react';
import { Outlet, useParams, useLocation } from 'react-router-dom';
import { Stepper, SessionSidebar, UserSessionsSidebar } from '../components';
import { agentCouncilAPI } from '../api';

export const SessionLayout = () => {
  const { sessionId } = useParams();
  const location = useLocation();
  const [sessionData, setSessionData] = useState(null);
  const [tokens, setTokens] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isPolling, setIsPolling] = useState(false);
  const pollingIntervalRef = useRef(null);
  
  // Determine current step from URL
  const getCurrentStep = () => {
    const path = location.pathname;
    if (path.includes('/build')) return 'build';
    if (path.includes('/edit')) return 'edit';
    if (path.includes('/execute')) return 'execute';
    if (path.includes('/review')) return 'review';
    return 'input';
  };
  
  // Fetch session data
  const fetchSessionData = async () => {
    try {
      const summary = await agentCouncilAPI.getSummary(sessionId);
      setSessionData(summary);
      if (summary.tokens) {
        setTokens(summary.tokens);
      }
      setLoading(false);
      return summary;
    } catch (err) {
      console.error('Failed to fetch session:', err);
      setLoading(false);
      throw err;
    }
  };
  
  // Start polling for active operations
  const startPolling = () => {
    if (pollingIntervalRef.current) return; // Already polling
    
    setIsPolling(true);
    pollingIntervalRef.current = setInterval(async () => {
      try {
        await fetchSessionData();
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 3000); // Poll every 3 seconds when active
  };
  
  // Stop polling
  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
      setIsPolling(false);
    }
  };
  
  // Initial fetch
  useEffect(() => {
    if (!sessionId) return;
    fetchSessionData();
    
    return () => {
      stopPolling();
    };
  }, [sessionId]);
  
  // Expose polling control to child components via context
  const contextValue = {
    sessionData,
    tokens,
    startPolling,
    stopPolling,
    isPolling,
    refreshSession: fetchSessionData
  };
  
  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">Loading session...</p>
        </div>
      </div>
    );
  }
  
  return (
    <>
      <Stepper currentStep={getCurrentStep()} />
      
      <div className="flex-1 flex">
        {/* Left Sidebar - User's Sessions */}
        <UserSessionsSidebar />
        
        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet context={contextValue} />
        </main>
        
        {/* Right Sidebar - Current Session Details */}
        {sessionData && (
          <SessionSidebar session={sessionData} tokens={tokens} />
        )}
      </div>
    </>
  );
};
