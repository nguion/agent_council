import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useOutletContext } from 'react-router-dom';
import { Loader2, Users, Brain, Search } from 'lucide-react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { agentCouncilAPI } from '../api';

export const Step2Build = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { sessionData, refreshSession } = useOutletContext();
  
  const [loading, setLoading] = useState(false);
  const [councilConfig, setCouncilConfig] = useState(null);
  const [error, setError] = useState(null);
  const [savingConfig, setSavingConfig] = useState(false);
  
  useEffect(() => {
    // Check if council already exists in session data
    if (sessionData?.council_config) {
      setCouncilConfig(sessionData.council_config);
    } else if (sessionId && !loading && !councilConfig) {
      // Only build if we don't have a config yet
      buildCouncil();
    }
  }, [sessionData, sessionId]);
  
  const buildCouncil = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const config = await agentCouncilAPI.buildCouncil(sessionId);
      
      if (config.error) {
        setError(config.error);
      } else {
        setCouncilConfig(config);
        // Refresh session data to update sidebar
        await refreshSession();
      }
    } catch (err) {
      console.error('Build council error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to build council';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSkipEditing = async () => {
    try {
      setSavingConfig(true);
      setError(null);
      await agentCouncilAPI.updateCouncil(sessionId, councilConfig);
      await refreshSession();
      navigate(`/sessions/${sessionId}/execute`);
    } catch (err) {
      console.error('Skip editing error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to save council configuration');
      setSavingConfig(false);
    }
  };
  
  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <Card>
          <div className="text-center py-12">
            <Loader2 className="h-16 w-16 text-primary-600 animate-spin mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Designing your council
            </h3>
            <p className="text-gray-600">
              The Architect is analyzing your question and context files to propose a set of specialized agents...
            </p>
          </div>
        </Card>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <Card>
          <div className="text-center py-12">
            <div className="text-red-600 mb-4">
              <Brain className="h-16 w-16 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">
                Failed to Build Council
              </h3>
              <p className="text-gray-600">{error}</p>
            </div>
            <div className="flex justify-center space-x-4 mt-6">
              <Button variant="secondary" onClick={() => navigate('/')}>
                Go Back
              </Button>
              <Button onClick={buildCouncil}>
                Try Again
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  }
  
  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          {councilConfig?.council_name || 'Your Council'}
        </h2>
        <p className="text-gray-600">
          {councilConfig?.strategy_summary}
        </p>
        <div className="mt-4">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary-100 text-primary-800">
            <Users className="h-4 w-4 mr-1" />
            {councilConfig?.agents?.length || 0} agents proposed
          </span>
        </div>
      </div>
      
      {/* Agent Grid */}
      <div className="grid grid-cols-1 gap-8 mb-12">
        {councilConfig?.agents?.map((agent, index) => (
          <Card key={index}>
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {agent.name}
                </h3>
                <div className="flex flex-wrap gap-2">
                  {agent.enable_web_search && (
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                      <Search className="h-3 w-3 mr-1" />
                      Web Search
                    </span>
                  )}
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    agent.reasoning_effort === 'high'
                      ? 'bg-purple-100 text-purple-800'
                      : agent.reasoning_effort === 'medium'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {agent.reasoning_effort || 'medium'} reasoning
                  </span>
                </div>
              </div>
              
              <div className="text-sm text-gray-600">
                <p className="line-clamp-3">{agent.persona}</p>
                <button 
                  className="text-primary-600 hover:text-primary-700 text-xs mt-1"
                  onClick={() => {
                    // Could expand to show full persona
                  }}
                >
                  View full persona →
                </button>
              </div>
            </div>
          </Card>
        ))}
      </div>
      
      {/* Error Display */}
      {error && (
        <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Actions */}
      <div className="bg-white rounded-lg shadow-md border-2 border-primary-200 p-6">
        <div className="flex justify-between items-center">
          <Button variant="secondary" onClick={() => navigate('/')} disabled={savingConfig}>
            ← Back
          </Button>
          <div className="flex space-x-3">
            <Button 
              variant="secondary" 
              onClick={handleSkipEditing}
              disabled={savingConfig || !councilConfig}
            >
              {savingConfig ? 'Saving...' : 'Skip Editing'}
            </Button>
            <Button 
              onClick={() => navigate(`/sessions/${sessionId}/edit`)}
              disabled={savingConfig || !councilConfig}
            >
              Review & Edit Council →
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
