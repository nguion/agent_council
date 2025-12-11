import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Clock, ArrowRight, FileText } from 'lucide-react';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { agentCouncilAPI } from '../api';

const stepRouteMap = {
  'input': 'build',
  'build': 'build',
  'edit': 'edit',
  'execute': 'execute',
  'review': 'review',
  'synthesize': 'review',
  'complete': 'review'
};

export const SessionsList = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await agentCouncilAPI.listSessions();
      setSessions(data.sessions || []);
    } catch (err) {
      setError(err.message || 'Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  const getStepLabel = (step) => {
    const labels = {
      'input': 'Input',
      'build': 'Build Council',
      'edit': 'Edit Council',
      'execute': 'Execute',
      'review': 'Review',
      'synthesize': 'Review',
      'complete': 'Complete'
    };
    return labels[step] || step;
  };

  const getStepColor = (step) => {
    if (step === 'complete') return 'bg-green-100 text-green-800';
    if (step === 'review' || step === 'synthesize') return 'bg-blue-100 text-blue-800';
    if (step === 'execute') return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <div className="max-w-6xl mx-auto py-12 px-4 w-full">
          <div className="text-center">
            <div className="animate-spin h-8 w-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading sessions...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col">
        <div className="max-w-6xl mx-auto py-12 px-4 w-full">
          <Card>
            <div className="text-center py-12">
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={loadSessions}>Try Again</Button>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto py-8 px-4">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Agent Council Sessions
              </h1>
              <p className="text-gray-600">
                View and resume your previous council sessions
              </p>
            </div>
            <Link to="/">
              <Button>
                <FileText className="h-4 w-4 mr-2" />
                New Session
              </Button>
            </Link>
          </div>
        </div>

        {sessions.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                No Sessions Yet
              </h3>
              <p className="text-gray-600 mb-6">
                Start your first Agent Council session to solve complex problems
              </p>
              <Link to="/">
                <Button>Create New Session</Button>
              </Link>
            </div>
          </Card>
        ) : (
          <div className="space-y-4">
            {sessions.map((session) => {
              const route = stepRouteMap[session.current_step] || 'build';
              const sessionUrl = `/sessions/${session.session_id}/${route}`;
              
              return (
                <Card key={session.session_id} className="hover:shadow-lg transition-shadow">
                  <Link to={sessionUrl}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getStepColor(session.current_step)}`}>
                            {getStepLabel(session.current_step)}
                          </span>
                          <span className="text-xs text-gray-500 flex items-center">
                            <Clock className="h-3 w-3 mr-1" />
                            {formatDate(session.created_at)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-900 font-medium mb-1">
                          {session.question}
                        </p>
                        <p className="text-xs text-gray-500">
                          Session ID: {session.session_id}
                        </p>
                      </div>
                      <div className="ml-4 flex-shrink-0">
                        <ArrowRight className="h-5 w-5 text-gray-400" />
                      </div>
                    </div>
                  </Link>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
