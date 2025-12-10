import React, { useState, useEffect } from 'react';
import { Loader2, Users, Brain, Search } from 'lucide-react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';

export const Step2Build = ({ sessionId, onNext, onBack }) => {
  const [loading, setLoading] = useState(true);
  const [councilConfig, setCouncilConfig] = useState(null);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    if (sessionId) {
      buildCouncil();
    }
  }, [sessionId]);
  
  const buildCouncil = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const { agentCouncilAPI } = await import('../api');
      const config = await agentCouncilAPI.buildCouncil(sessionId);
      
      if (config.error) {
        setError(config.error);
      } else {
        setCouncilConfig(config);
      }
    } catch (err) {
      setError(err.message || 'Failed to build council');
    } finally {
      setLoading(false);
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
              <Button variant="secondary" onClick={onBack}>
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
      <div className="grid grid-cols-1 gap-6 mb-8">
        {councilConfig?.agents?.map((agent, index) => (
          <Card key={index}>
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {agent.name}
                </h3>
                <div className="flex space-x-2">
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
      
      {/* Actions */}
      <div className="bg-white rounded-lg shadow-md border-2 border-primary-200 p-6">
        <div className="flex justify-between items-center">
          <Button variant="secondary" onClick={onBack}>
            ← Back
          </Button>
          <div className="flex space-x-3">
            <Button variant="secondary" onClick={() => onNext(councilConfig, true)}>
              Skip Editing
            </Button>
            <Button onClick={() => onNext(councilConfig, false)}>
              Review & Edit Council →
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
