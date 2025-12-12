import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, useOutletContext } from 'react-router-dom';
import { Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import ReactMarkdown from 'react-markdown';
import { agentCouncilAPI } from '../api';

export const Step5Review = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { sessionData, startPolling, stopPolling, refreshSession } = useOutletContext();
  
  const [reviewStatus, setReviewStatus] = useState('idle');
  const [reviews, setReviews] = useState(null);
  const [aggregatedScores, setAggregatedScores] = useState(null);
  const [reviewStatuses, setReviewStatuses] = useState({});
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
      
      const response = await agentCouncilAPI.startPeerReview(sessionId, force);
      
      // Check if review was already done
      if (response.status === 'already_reviewed' && !force) {
        const reviewData = await agentCouncilAPI.getReviews(sessionId);
        setReviews(reviewData.reviews);
        setAggregatedScores(reviewData.aggregated_scores);
        setReviewStatus('completed');
        setError('Peer review already completed. You can proceed to synthesis or re-run the review.');
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
            // If synthesis is next, encourage navigation
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
      const rawDetail = err.response?.data?.detail || err.message || 'Failed to start peer review';
      const errorMessage = Array.isArray(rawDetail)
        ? rawDetail.map((d) => d?.msg || JSON.stringify(d)).join('; ')
        : typeof rawDetail === 'object'
        ? JSON.stringify(rawDetail)
        : rawDetail;
      setError(errorMessage);
      setReviewStatus('error');
      if (pollingInterval.current) {
        clearInterval(pollingInterval.current);
        pollingInterval.current = null;
      }
      stopPolling();
    }
  };
  
  const goToSynthesize = () => {
    setError(null);
    navigate(`/sessions/${sessionId}/synthesize`);
  };
  
  // Require execution results before peer review
  if (!sessionData?.execution_results) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <Card>
          <div className="text-center py-12">
            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
              Execution Required
            </h3>
            <p className="text-gray-600 mb-8">
              Run the council execution before starting peer review.
            </p>
            <Button onClick={() => navigate(`/sessions/${sessionId}/execute`)}>
              Go to Execute
            </Button>
          </div>
        </Card>
      </div>
    );
  }

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
              <Button onClick={() => startPeerReview()}>
                Start Peer Review
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (reviewStatus === 'error') {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <Card>
          <div className="text-center py-12">
            <h3 className="text-2xl font-semibold text-gray-900 mb-3">
              Peer Review Failed
            </h3>
            <p className="text-gray-600 mb-6">
              {error || 'Peer review encountered an issue. You can retry the review or return to execution results.'}
            </p>
            <div className="flex justify-center space-x-3">
              <Button onClick={() => startPeerReview(true)}>
                Retry Review
              </Button>
              <Button variant="secondary" onClick={() => navigate(`/sessions/${sessionId}/execute`)}>
                Back to Execution
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
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Peer Review Complete
          </h2>
          <p className="text-gray-600">
            {reviews?.length || 0} critiques generated
          </p>
        </div>
        <div className="flex space-x-3">
          <Button variant="secondary" onClick={() => startPeerReview(true)}>
            Re-run Review
          </Button>
          <Button onClick={goToSynthesize}>
            Proceed to Synthesize →
          </Button>
        </div>
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
      
    </div>
  );
};
