import React, { useEffect, useState } from 'react';
import { useNavigate, useOutletContext, useParams } from 'react-router-dom';
import { Award, Copy, Download, Loader2, RefreshCw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { agentCouncilAPI } from '../api';

export const Step6Synthesize = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { sessionData, refreshSession } = useOutletContext();

  const [verdictStatus, setVerdictStatus] = useState('idle');
  const [verdict, setVerdict] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (sessionData?.chairman_verdict) {
      setVerdict(sessionData.chairman_verdict);
      setVerdictStatus('completed');
    }
  }, [sessionData]);

  const startSynthesis = async (force = false) => {
    if (!sessionData?.peer_reviews) {
      setError('Peer reviews are required before synthesis. Complete the Review step first.');
      return;
    }

    try {
      setVerdictStatus('synthesizing');
      setError(null);

      const result = await agentCouncilAPI.synthesize(sessionId, force);
      setVerdict(result.verdict);
      setVerdictStatus('completed');

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

  if (!sessionData?.peer_reviews && verdictStatus === 'idle') {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <Card>
          <div className="text-center py-12">
            <h3 className="text-2xl font-semibold text-gray-900 mb-4">Peer Review Required</h3>
            <p className="text-gray-600 mb-8">
              Complete the Review step to gather peer critiques before generating the Chairman&apos;s verdict.
            </p>
            <Button onClick={() => navigate(`/sessions/${sessionId}/review`)}>
              Go to Review
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (verdictStatus === 'idle' && !verdict) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <Card>
          <div className="text-center py-12 space-y-4">
            <h3 className="text-2xl font-semibold text-gray-900">Ready to Synthesize</h3>
            <p className="text-gray-600">
              The Chairman will synthesize all proposals and peer critiques into a final verdict.
            </p>
            <div className="flex justify-center space-x-3">
              <Button onClick={() => startSynthesis()}>
                <Award className="h-5 w-5 mr-2" />
                Generate Verdict
              </Button>
              <Button variant="secondary" onClick={() => startSynthesis(true)}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Re-run (Force)
              </Button>
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        </Card>
      </div>
    );
  }

  if (verdictStatus === 'synthesizing') {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <Card>
          <div className="text-center py-12">
            <Loader2 className="h-16 w-16 text-primary-600 animate-spin mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              The Chairman is synthesizing the final verdict...
            </h3>
            <p className="text-gray-600">Integrating all proposals and peer critiques</p>
            {error && <p className="text-sm text-red-600 mt-4">{error}</p>}
          </div>
        </Card>
      </div>
    );
  }

  if (verdictStatus === 'error') {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <Card>
          <div className="text-center py-12 space-y-4">
            <h3 className="text-2xl font-semibold text-gray-900">Synthesis Failed</h3>
            <p className="text-gray-600">{error}</p>
            <div className="flex justify-center space-x-3">
              <Button onClick={() => startSynthesis(true)}>
                Retry Synthesis
              </Button>
              <Button variant="secondary" onClick={() => navigate(`/sessions/${sessionId}/review`)}>
                Back to Review
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Chairman&apos;s Final Verdict</h2>
          <p className="text-gray-600">Rendered after integrating proposals and peer critiques.</p>
        </div>
        <div className="flex space-x-3">
          <Button variant="secondary" onClick={() => startSynthesis(true)}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Re-run Verdict
          </Button>
          <Button onClick={() => navigate(`/sessions/${sessionId}/review`)}>
            View Peer Reviews
          </Button>
        </div>
      </div>

      {error && (
        <Card className="mb-6">
          <p className="text-sm text-red-600">{error}</p>
        </Card>
      )}

      {verdict && (
        <Card>
          <div className="prose prose-base max-w-none text-gray-900 max-h-[70vh] overflow-y-auto pr-2">
            <ReactMarkdown
              components={{
                h1: ({ node: _node, ...props }) => <h1 className="text-2xl font-bold mb-4 mt-6 text-gray-900 border-b border-primary-200 pb-2" {...props} />,
                h2: ({ node: _node, ...props }) => <h2 className="text-xl font-semibold mb-3 mt-5 text-gray-800" {...props} />,
                h3: ({ node: _node, ...props }) => <h3 className="text-lg font-semibold mb-2 mt-4 text-gray-800" {...props} />,
                p: ({ node: _node, ...props }) => <p className="mb-3 leading-relaxed text-gray-700" {...props} />,
                ul: ({ node: _node, ...props }) => <ul className="mb-3 ml-5 space-y-1 list-disc [&_ul]:mt-1 [&_ul]:mb-1 [&_ul]:ml-5 [&_ul]:list-circle [&_ul_ul]:list-square" {...props} />,
                ol: ({ node: _node, ...props }) => <ol className="mb-3 ml-5 space-y-1 list-decimal [&_ol]:mt-1 [&_ol]:mb-1 [&_ol]:ml-5 [&_ol]:list-[lower-alpha] [&_ol_ol]:list-[lower-roman]" {...props} />,
                li: ({ node: _node, ...props }) => <li className="leading-relaxed text-gray-700 [&>ul]:mt-1 [&>ol]:mt-1" {...props} />,
                strong: ({ node: _node, ...props }) => <strong className="font-semibold text-gray-900" {...props} />,
                em: ({ node: _node, ...props }) => <em className="italic text-gray-800" {...props} />,
                blockquote: ({ node: _node, ...props }) => <blockquote className="border-l-4 border-primary-300 pl-4 py-2 my-3 italic text-gray-600 bg-gray-50 rounded-r" {...props} />,
                code: ({ node: _node, inline, ...props }) =>
                  inline
                    ? <code className="px-1.5 py-0.5 bg-gray-100 text-primary-700 rounded text-sm font-mono" {...props} />
                    : <code className="block p-3 bg-gray-900 text-gray-100 rounded-lg overflow-x-auto text-sm font-mono my-3" {...props} />,
                pre: ({ node: _node, ...props }) => <pre className="my-3" {...props} />,
                hr: ({ node: _node, ...props }) => <hr className="my-4 border-gray-200" {...props} />,
              }}
            >
              {verdict}
            </ReactMarkdown>
          </div>
          <div className="mt-6 pt-4 border-t border-gray-200 flex space-x-4">
            <Button variant="secondary" onClick={() => copyToClipboard(verdict)}>
              <Copy className="h-4 w-4 mr-1" />
              Copy Verdict
            </Button>
            <Button variant="secondary" onClick={downloadSession}>
              <Download className="h-4 w-4 mr-1" />
              Download Full Session
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
};


