import React, { useState, useEffect, useRef } from 'react';
import { Loader2, CheckCircle2, XCircle, Eye, Copy, Search } from 'lucide-react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import ReactMarkdown from 'react-markdown';

export const Step4Execute = ({ sessionId, onNext, onBack }) => {
  const [status, setStatus] = useState('idle');
  const [results, setResults] = useState(null);
  const [agentStatuses, setAgentStatuses] = useState({});
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [error, setError] = useState(null);
  const pollingInterval = useRef(null);
  
  useEffect(() => {
    return () => {
      if (pollingInterval.current) {
        clearInterval(pollingInterval.current);
      }
    };
  }, []);
  
  const startExecution = async () => {
    try {
      setStatus('starting');
      setError(null);
      
      const { agentCouncilAPI } = await import('../api');
      await agentCouncilAPI.executeCouncil(sessionId);
      
      setStatus('executing');
      
      // Start polling for status
      pollingInterval.current = setInterval(async () => {
        try {
          const statusData = await agentCouncilAPI.getStatus(sessionId);
          setAgentStatuses(statusData.execution_status || {});
          
          if (statusData.status === 'execution_complete') {
            clearInterval(pollingInterval.current);
            const resultsData = await agentCouncilAPI.getResults(sessionId);
            setResults(resultsData);
            setStatus('completed');
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }, 1500);
      
    } catch (err) {
      setError(err.message || 'Failed to start execution');
      setStatus('error');
    }
  };
  
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };
  
  const getStatusColor = (status) => {
    if (status === 'Done' || status === 'success') return 'text-green-600';
    if (status === 'Failed' || status === 'error') return 'text-red-600';
    if (status === 'Thinking & Searching...' || status === 'Initializing...') return 'text-blue-600';
    return 'text-gray-600';
  };
  
  const getStatusIcon = (status) => {
    if (status === 'Done' || status === 'success') return <CheckCircle2 className="h-5 w-5" />;
    if (status === 'Failed' || status === 'error') return <XCircle className="h-5 w-5" />;
    return <Loader2 className="h-5 w-5 animate-spin" />;
  };
  
  if (status === 'idle') {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <Card>
          <div className="text-center py-12">
            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
              Ready to Launch Council
            </h3>
            <p className="text-gray-600 mb-8">
              All agents will run in parallel on your question and context. You can watch their progress in real-time.
            </p>
            <div className="flex justify-center space-x-4">
              <Button variant="secondary" onClick={onBack}>
                Back to Edit
              </Button>
              <Button onClick={startExecution}>
                Start Execution
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  }
  
  if (status === 'error') {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <Card>
          <div className="text-center py-12">
            <XCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Execution Failed
            </h3>
            <p className="text-gray-600 mb-8">{error}</p>
            <div className="flex justify-center space-x-4">
              <Button variant="secondary" onClick={onBack}>
                Go Back
              </Button>
              <Button onClick={startExecution}>
                Try Again
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  }
  
  if (status === 'starting' || (status === 'executing' && !results)) {
    // Filter out 'ALL' from agent statuses
    const filteredStatuses = Object.entries(agentStatuses).filter(([name]) => name !== 'ALL');
    
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <div className="mb-8 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Council Execution in Progress
          </h2>
          <p className="text-gray-600">
            {filteredStatuses.length > 0
              ? `${filteredStatuses.filter(([_, s]) => s === 'Done').length} of ${filteredStatuses.length} agents complete`
              : 'Initializing agents...'}
          </p>
        </div>
        
        {/* Agent Status Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredStatuses.map(([agentName, agentStatus]) => (
            <Card key={agentName}>
              <div className="flex items-center space-x-3">
                <div className={getStatusColor(agentStatus)}>
                  {getStatusIcon(agentStatus)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {agentName}
                  </p>
                  <p className={`text-xs ${getStatusColor(agentStatus)}`}>
                    {agentStatus}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }
  
  // Execution complete - show results
  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Execution Complete
            </h2>
            <p className="text-gray-600">
              All agents have completed their analysis. Review their responses below.
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">
              {results?.execution_results?.filter(r => r.status === 'success').length || 0} succeeded,{' '}
              {results?.execution_results?.filter(r => r.status === 'error').length || 0} failed
            </div>
          </div>
        </div>
        
        {/* Filters */}
        <div className="flex space-x-2">
          <button className="px-3 py-1 text-sm rounded-full bg-primary-100 text-primary-800 font-medium">
            All
          </button>
          <button className="px-3 py-1 text-sm rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200">
            Success
          </button>
          <button className="px-3 py-1 text-sm rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200">
            Failed
          </button>
        </div>
      </div>
      
      {/* Results List */}
      <div className="space-y-4 mb-8">
        {results?.execution_results?.map((result, index) => (
          <Card key={index}>
            <div className="space-y-3">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {result.agent_name}
                    </h3>
                    {result.status === 'success' ? (
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-600" />
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Proposal #{result.proposal_id}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  {result.tools_used?.includes('web_search_call') && (
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                      <Search className="h-3 w-3 mr-1" />
                      Used Web Search
                    </span>
                  )}
                </div>
              </div>
              
              {/* TLDR */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-sm font-medium text-gray-700 mb-2">TL;DR</p>
                <div className="text-sm text-gray-900 prose prose-sm max-w-none">
                  <ReactMarkdown>{result.tldr}</ReactMarkdown>
                </div>
              </div>
              
              {/* Actions */}
              <div className="flex space-x-2">
                <Button
                  variant="secondary"
                  onClick={() => setSelectedAgent(result)}
                  className="text-sm py-2"
                >
                  <Eye className="h-4 w-4 mr-1" />
                  View Full Response
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => copyToClipboard(result.response)}
                  className="text-sm py-2"
                >
                  <Copy className="h-4 w-4 mr-1" />
                  Copy
                </Button>
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
          <Button onClick={onNext}>
            Run Peer Review →
          </Button>
        </div>
      </div>
      
      {/* Full Response Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">
                  {selectedAgent.agent_name}
                </h3>
                <p className="text-sm text-gray-500">Full Response</p>
              </div>
              <button
                onClick={() => setSelectedAgent(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XCircle className="h-6 w-6" />
              </button>
            </div>
            
            <div className="p-6">
              <div className="prose prose-lg max-w-none text-gray-900">
                <ReactMarkdown>{selectedAgent.response}</ReactMarkdown>
              </div>
            </div>
            
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-4 sticky bottom-0 bg-white">
              <Button variant="secondary" onClick={() => copyToClipboard(selectedAgent.response)}>
                <Copy className="h-4 w-4 mr-1" />
                Copy
              </Button>
              <Button onClick={() => setSelectedAgent(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
