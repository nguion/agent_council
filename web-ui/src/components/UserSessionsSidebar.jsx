import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Plus, Trash2, Clock, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
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

export const UserSessionsSidebar = () => {
  const { sessionId: currentSessionId } = useParams();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    loadSessions();
    
    // Refresh sessions list every 10 seconds
    const interval = setInterval(loadSessions, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadSessions = async () => {
    try {
      setError(null);
      const data = await agentCouncilAPI.listSessions();
      setSessions(data.sessions || []);
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Failed to load sessions');
      setLoading(false);
    }
  };

  const deleteSession = async (sessionId, e) => {
    e.stopPropagation();
    
    if (!window.confirm('Delete this session? Files will be preserved but it will be hidden from your list.')) {
      return;
    }
    
    try {
      setDeletingId(sessionId);
      await agentCouncilAPI.deleteSession(sessionId);
      
      // Remove from local list
      setSessions(sessions.filter(s => s.session_id !== sessionId));
      
      // If we just deleted the current session, navigate to sessions list
      if (sessionId === currentSessionId) {
        navigate('/sessions');
      }
    } catch (err) {
      alert('Failed to delete session: ' + err.message);
    } finally {
      setDeletingId(null);
    }
  };

  const getStatusIcon = (step, status) => {
    if (step === 'complete') return <CheckCircle className="h-4 w-4 text-green-600" />;
    if (status === 'executing' || status === 'reviewing') return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
    return <Clock className="h-4 w-4 text-gray-400" />;
  };

  const getStepLabel = (step) => {
    const labels = {
      'input': 'Input',
      'build': 'Build',
      'edit': 'Edit',
      'execute': 'Execute',
      'review': 'Review',
      'synthesize': 'Review',
      'complete': 'Complete'
    };
    return labels[step] || step;
  };

  const getStepColor = (step) => {
    if (step === 'complete') return 'bg-green-100 text-green-800 border-green-200';
    if (step === 'review' || step === 'synthesize') return 'bg-blue-100 text-blue-800 border-blue-200';
    if (step === 'execute') return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    return 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const formatTime = (isoString) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const formatCost = (cost) => {
    if (!cost) return null;
    return `$${cost.toFixed(3)}`;
  };

  if (loading) {
    return (
      <div className="w-80 bg-gray-50 border-r border-gray-200 p-4 overflow-y-auto">
        <div className="text-center py-12">
          <Loader2 className="h-8 w-8 text-primary-600 animate-spin mx-auto mb-2" />
          <p className="text-sm text-gray-600">Loading sessions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-80 bg-gray-50 border-r border-gray-200 p-4 overflow-y-auto">
        <div className="text-center py-8">
          <AlertCircle className="h-8 w-8 text-red-600 mx-auto mb-2" />
          <p className="text-sm text-red-600 mb-4">{error}</p>
          <button
            onClick={loadSessions}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
            My Sessions
          </h2>
          <button
            onClick={() => navigate('/')}
            className="p-1.5 text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
            title="New Session"
          >
            <Plus className="h-5 w-5" />
          </button>
        </div>
        <p className="text-xs text-gray-500">
          {sessions.length} session{sessions.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="p-4 text-center">
            <p className="text-sm text-gray-600 mb-4">No sessions yet</p>
            <button
              onClick={() => navigate('/')}
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              Create your first session
            </button>
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {sessions.map((session) => {
              const route = stepRouteMap[session.current_step] || 'build';
              const sessionUrl = `/sessions/${session.session_id}/${route}`;
              const isActive = session.session_id === currentSessionId;
              const cost = formatCost(session.last_cost_usd);
              
              return (
                <div
                  key={session.session_id}
                  className={`group relative rounded-lg border transition-all cursor-pointer ${
                    isActive
                      ? 'bg-primary-50 border-primary-300 shadow-sm'
                      : 'bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300'
                  }`}
                  onClick={() => navigate(sessionUrl)}
                >
                  <div className="p-3">
                    {/* Top row: status and time */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(session.current_step, session.status)}
                        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${getStepColor(session.current_step)}`}>
                          {getStepLabel(session.current_step)}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {formatTime(session.updated_at)}
                      </span>
                    </div>

                    {/* Question */}
                    <p className={`text-sm leading-snug mb-2 ${
                      isActive ? 'text-gray-900 font-medium' : 'text-gray-700'
                    }`}>
                      {session.question.length > 80
                        ? `${session.question.substring(0, 80)}...`
                        : session.question}
                    </p>

                    {/* Bottom row: cost and delete */}
                    <div className="flex items-center justify-between">
                      {cost && (
                        <span className="text-xs text-gray-500 font-mono">
                          {cost}
                        </span>
                      )}
                      <button
                        onClick={(e) => deleteSession(session.session_id, e)}
                        className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-all"
                        title="Delete session"
                        disabled={deletingId === session.session_id}
                      >
                        {deletingId === session.session_id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-200 bg-white">
        <button
          onClick={() => navigate('/sessions')}
          className="w-full text-sm text-center text-primary-600 hover:text-primary-700 font-medium py-2"
        >
          View All Sessions →
        </button>
      </div>
    </div>
  );
};
