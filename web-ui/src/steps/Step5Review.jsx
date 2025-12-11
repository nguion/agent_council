import React, { useState, useEffect, useRef } from 'react';
import { useParams, useOutletContext } from 'react-router-dom';
import { Loader2, Award, Download, Copy, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import ReactMarkdown from 'react-markdown';
import { agentCouncilAPI } from '../api';

export const Step5Review = () => {
  const { sessionId } = useParams();
  const { sessionData, startPolling, stopPolling, refreshSession } = useOutletContext();
  
  const [reviewStatus, setReviewStatus] = useState('idle');
  const [reviews, setReviews] = useState(null);
  const [aggregatedScores, setAggregatedScores] = useState(null);
  const [reviewStatuses, setReviewStatuses] = useState({});
  const [verdictStatus, setVerdictStatus] = useState('idle');
  const [verdict, setVerdict] = useState(null);
  const [expandedProposal, setExpandedProposal] = useState(null);
  const [error, setError] = useState(null);
  const pollingInterval = useRef(null);
  
  useEffect(() => {
    // Check if peer reviews already exist
    if (sessionData?.peer_reviews) {
      setReviews(sessionData.peer_reviews);
      setAggregatedScores(sessionData.aggregated_scores || {});
      setReviewStatus('completed');
      stopPolling();
    }
    
    // Check if verdict already exists
    if (sessionData?.chairman_verdict) {
      setVerdict(sessionData.chairman_verdict);
      setVerdictStatus('completed');
    }
  }, [sessionData]);
  
  useEffect(() => {
    return () => {
      if (pollingInterval.current) {
        clearInterval(pollingInterval.current);
      }
      stopPolling();
    };
  }, []);
  
  const startPeerReview = async (force = false) => {
    try {
      setReviewStatus('starting');
      setError(null);
      
      const response = await agentCouncilAPI.startPeerReview(sessionId);
      
      // Check if review was already done
      if (response.status === 'already_reviewed' && !force) {
        setError('Peer review already completed. Reload the page to see results.');
        setReviewStatus('error');
        await refreshSession();
        return;
      }
      
      setReviewStatus('reviewing');
      
      // Start controlled polling
      startPolling();
      
      // Poll for review status
      pollingInterval.current = setInterval(async () => {
        try {
          const statusData = await agentCouncilAPI.getStatus(sessionId);
          setReviewStatuses(statusData.review_status || {});
          
          if (statusData.status === 'review_complete') {
            clearInterval(pollingInterval.current);
            pollingInterval.current = null;
            stopPolling();
            
            const reviewData = await agentCouncilAPI.getReviews(sessionId);
            setReviews(reviewData.reviews);
            setAggregatedScores(reviewData.aggregated_scores);
            setReviewStatus('completed');
            
            // Refresh session data
            await refreshSession();
          } else if (statusData.status === 'review_error') {
            clearInterval(pollingInterval.current);
            pollingInterval.current = null;
            stopPolling();
            setError('Peer review encountered an error. Please check the logs and try again.');
            setReviewStatus('error');
          }
        } catch (err) {
          console.error('Polling error:', err);
          // Don't stop polling on transient errors
        }
      }, 1500);
      
    } catch (err) {
      console.error('Start peer review error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to start peer review';
      setError(errorMessage);
      setReviewStatus('error');
      if (pollingInterval.current) {
        clearInterval(pollingInterval.current);
        pollingInterval.current = null;
      }
      stopPolling();
    }
  };
  
  const startSynthesis = async (force = false) => {
    try {
      setVerdictStatus('synthesizing');
      setError(null);
      
      const result = await agentCouncilAPI.synthesize(sessionId);
      
      setVerdict(result.verdict);
      setVerdictStatus('completed');
      
      // Refresh session data to update sidebar
      await refreshSession();
      
    } catch (err) {
      console.error('Synthesis error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to synthesize verdict';
      setError(errorMessage);
      setVerdictStatus('error');
    }
  };
  
  const downloadSession = async () => {
    try {
      const summary = await agentCouncilAPI.getSummary(sessionId);
      
      const blob = new Blob([JSON.stringify(summary, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `council_session_${sessionId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to download session: ' + err.message);
    }
  };
  
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };
  
  // Start peer review state
  if (reviewStatus === 'idle') {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <Card>
          <div className="text-center py-12">
            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
              Ready for Peer Review
            </h3>
            <p className="text-gray-600 mb-8">
              Each agent will now review the proposals from their peers and provide structured critiques.
            </p>
            <div className="flex justify-center">
              <Button onClick={startPeerReview}>
                Start Peer Review
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  }
  
  // Reviewing in progress
  if (reviewStatus === 'starting' || (reviewStatus === 'reviewing' && !reviews)) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <div className="mb-8 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Peer Review in Progress
          </h2>
          <p className="text-gray-600">
            {Object.keys(reviewStatuses).length > 0
              ? `${Object.values(reviewStatuses).filter(s => s === 'Critique Complete').length} of ${Object.keys(reviewStatuses).length} reviews complete`
              : 'Initializing peer review...'}
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(reviewStatuses).map(([agentName, status]) => (
            <Card key={agentName}>
              <div className="flex items-center space-x-3">
                <Loader2 className={`h-5 w-5 ${status === 'Critique Complete' ? 'text-green-600' : 'text-blue-600 animate-spin'}`} />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{agentName}</p>
                  <p className="text-xs text-gray-500">{status}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }
  
  // Reviews complete, show scores and verdict
  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          Peer Review Complete
        </h2>
        <p className="text-gray-600">
          {reviews?.length || 0} critiques generated
        </p>
      </div>
      
      {/* Scores Table */}
      {aggregatedScores && (
        <Card title="Peer Review Scores by Proposal" className="mb-8">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    Proposal
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    Avg Score
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    # Reviews
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    Sample Comment
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {Object.entries(aggregatedScores).map(([proposalId, data], index) => {
                  const avgScore = data.scores.length > 0
                    ? (data.scores.reduce((a, b) => a + b, 0) / data.scores.length).toFixed(2)
                    : 'N/A';
                  const sampleComment = data.comments.filter(c => c).length > 0
                    ? data.comments.filter(c => c)[0].substring(0, 80) + '...'
                    : 'No comments';
                  
                  return (
                    <tr 
                      key={proposalId} 
                      className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                        index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                      }`}
                    >
                      <td className="px-6 py-5 whitespace-nowrap text-sm font-semibold text-gray-900">
                        Proposal #{proposalId}
                      </td>
                      <td className="px-6 py-5 whitespace-nowrap">
                        <span className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-bold ${
                          parseFloat(avgScore) >= 4
                            ? 'bg-primary-100 text-primary-800'
                            : parseFloat(avgScore) >= 3
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {avgScore}
                        </span>
                      </td>
                      <td className="px-6 py-5 whitespace-nowrap text-sm font-medium text-gray-700">
                        {data.scores.length}
                      </td>
                      <td className="px-6 py-5 text-sm text-gray-600 max-w-lg">
                        <p className="line-clamp-2">{sampleComment}</p>
                      </td>
                      <td className="px-6 py-5 whitespace-nowrap text-right">
                        <button
                          onClick={() => setExpandedProposal(expandedProposal === proposalId ? null : proposalId)}
                          className="inline-flex items-center px-4 py-2 text-sm font-medium text-primary-700 hover:text-primary-900 hover:bg-primary-50 rounded-lg transition-colors"
                        >
                          {expandedProposal === proposalId ? (
                            <>
                              Hide Details
                              <ChevronUp className="h-4 w-4 ml-1" />
                            </>
                          ) : (
                            <>
                              View Details
                              <ChevronDown className="h-4 w-4 ml-1" />
                            </>
                          )}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          
          {/* Expanded Details */}
          {expandedProposal && reviews && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h4 className="font-medium text-gray-900 mb-4">
                Detailed Critiques for Proposal #{expandedProposal}
              </h4>
              <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                {reviews.map((review, idx) => {
                  const proposalReview = review.parsed?.per_proposal?.find(
                    p => p.proposal_id === parseInt(expandedProposal)
                  );
                  
                  if (!proposalReview) return null;
                  
                  return (
                    <div key={idx} className="bg-white p-4 rounded border border-gray-200">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-700">
                          Reviewer {idx + 1}
                        </span>
                        <span className="text-sm font-semibold text-gray-900">
                          Score: {proposalReview.score}/5
                        </span>
                      </div>
                      <div className="space-y-3 text-sm">
                        <div>
                          <span className="font-medium text-green-700">Strengths:</span>
                          <div className="text-gray-600 mt-1 prose prose-sm max-w-none">
                            <ReactMarkdown>{proposalReview.strengths}</ReactMarkdown>
                          </div>
                        </div>
                        <div>
                          <span className="font-medium text-red-700">Weaknesses:</span>
                          <div className="text-gray-600 mt-1 prose prose-sm max-w-none">
                            <ReactMarkdown>{proposalReview.weaknesses}</ReactMarkdown>
                          </div>
                        </div>
                        <div>
                          <span className="font-medium text-yellow-700">Gaps/Risks:</span>
                          <div className="text-gray-600 mt-1 prose prose-sm max-w-none">
                            <ReactMarkdown>{proposalReview.gaps_risks}</ReactMarkdown>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </Card>
      )}
      
      {/* Chairman's Verdict */}
      {verdictStatus === 'idle' && (
        <div className="flex justify-center mb-8">
          <Button onClick={startSynthesis}>
            <Award className="h-5 w-5 mr-2" />
            Generate Chairman's Verdict
          </Button>
        </div>
      )}
      
      {verdictStatus === 'synthesizing' && (
        <Card className="mb-8">
          <div className="text-center py-12">
            <Loader2 className="h-16 w-16 text-primary-600 animate-spin mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              The Chairman is synthesizing the final verdict...
            </h3>
            <p className="text-gray-600">
              Integrating all proposals and peer critiques
            </p>
          </div>
        </Card>
      )}
      
      {verdictStatus === 'completed' && verdict && (
        <Card title="Chairman's Final Verdict" className="mb-8">
          <div className="prose prose-base max-w-none text-gray-900 max-h-[70vh] overflow-y-auto pr-2">
            <ReactMarkdown
              components={{
                h1: ({node, ...props}) => <h1 className="text-2xl font-bold mb-4 mt-6 text-gray-900 border-b border-primary-200 pb-2" {...props} />,
                h2: ({node, ...props}) => <h2 className="text-xl font-semibold mb-3 mt-5 text-gray-800" {...props} />,
                h3: ({node, ...props}) => <h3 className="text-lg font-semibold mb-2 mt-4 text-gray-800" {...props} />,
                p: ({node, ...props}) => <p className="mb-3 leading-relaxed text-gray-700" {...props} />,
                ul: ({node, ...props}) => <ul className="mb-3 ml-5 space-y-1 list-disc [&_ul]:mt-1 [&_ul]:mb-1 [&_ul]:ml-5 [&_ul]:list-circle [&_ul_ul]:list-square" {...props} />,
                ol: ({node, ...props}) => <ol className="mb-3 ml-5 space-y-1 list-decimal [&_ol]:mt-1 [&_ol]:mb-1 [&_ol]:ml-5 [&_ol]:list-[lower-alpha] [&_ol_ol]:list-[lower-roman]" {...props} />,
                li: ({node, ...props}) => <li className="leading-relaxed text-gray-700 [&>ul]:mt-1 [&>ol]:mt-1" {...props} />,
                strong: ({node, ...props}) => <strong className="font-semibold text-gray-900" {...props} />,
                em: ({node, ...props}) => <em className="italic text-gray-800" {...props} />,
                blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-primary-300 pl-4 py-2 my-3 italic text-gray-600 bg-gray-50 rounded-r" {...props} />,
                code: ({node, inline, ...props}) => 
                  inline 
                    ? <code className="px-1.5 py-0.5 bg-gray-100 text-primary-700 rounded text-sm font-mono" {...props} />
                    : <code className="block p-3 bg-gray-900 text-gray-100 rounded-lg overflow-x-auto text-sm font-mono my-3" {...props} />,
                pre: ({node, ...props}) => <pre className="my-3" {...props} />,
                hr: ({node, ...props}) => <hr className="my-4 border-gray-200" {...props} />,
              }}
            >
              {verdict}
            </ReactMarkdown>
          </div>
          <div className="mt-6 pt-4 border-t border-gray-200 flex space-x-4">
            <Button
              variant="secondary"
              onClick={() => copyToClipboard(verdict)}
            >
              <Copy className="h-4 w-4 mr-1" />
              Copy Verdict
            </Button>
            <Button
              variant="secondary"
              onClick={downloadSession}
            >
              <Download className="h-4 w-4 mr-1" />
              Download Full Session
            </Button>
          </div>
        </Card>
      )}
      
      {/* Completion Badge */}
      <div className="bg-white rounded-lg shadow-md border-2 border-primary-200 p-6">
        <div className="flex items-center justify-end gap-3">
            {verdictStatus === 'completed' && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800 whitespace-nowrap">
                ✓ Session Complete
              </span>
            )}
        </div>
      </div>
    </div>
  );
};
