import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Outlet, useParams, useLocation, useNavigate } from 'react-router-dom';
import { Stepper, SessionSidebar, UserSessionsSidebar } from '../components';
import { agentCouncilAPI } from '../api';
import { Menu, ChevronLeft, ChevronRight } from 'lucide-react';

const LEFT_SIDEBAR_KEY = 'agent_council_left_sidebar_visible';
const RIGHT_SIDEBAR_KEY = 'agent_council_right_sidebar_visible';
const LEFT_WIDTH_KEY = 'agent_council_left_sidebar_width';
const RIGHT_WIDTH_KEY = 'agent_council_right_sidebar_width';
const RIGHT_BREAKPOINT = 1200; // hide right pane first on narrow view
const LEFT_BREAKPOINT = 992;   // hide left pane second on narrow view
const MIN_LEFT_WIDTH = 240;
const MAX_LEFT_WIDTH = 420;
const MIN_RIGHT_WIDTH = 240;
const MAX_RIGHT_WIDTH = 420;

export const SessionLayout = () => {
  const { sessionId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [sessionData, setSessionData] = useState(null);
  const [tokens, setTokens] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isPolling, setIsPolling] = useState(false);
  const pollingIntervalRef = useRef(null);
  const leftPrefRef = useRef(true);
  const rightPrefRef = useRef(true);
  const [leftVisible, setLeftVisible] = useState(true);
  const [rightVisible, setRightVisible] = useState(true);
  const [leftWidth, setLeftWidth] = useState(300);
  const [rightWidth, setRightWidth] = useState(320);
  const dragStateRef = useRef({ side: null, startX: 0, startWidth: 0 });
  
  // Determine current step from URL
  const getCurrentStep = () => {
    const path = location.pathname;
    if (path.includes('/build')) return 'build';
    if (path.includes('/edit')) return 'edit';
    if (path.includes('/execute')) return 'execute';
    if (path.includes('/review')) return 'review';
    return 'input';
  };

  const stepOrder = ['input', 'build', 'edit', 'execute', 'review'];

  const stepPaths = {
    input: '/',
    build: sessionId ? `/sessions/${sessionId}/build` : '/',
    edit: sessionId ? `/sessions/${sessionId}/edit` : '/',
    execute: sessionId ? `/sessions/${sessionId}/execute` : '/',
    review: sessionId ? `/sessions/${sessionId}/review` : '/',
  };

  const computeAllowedSteps = () => {
    let highestIndex = 0;

    // Use server-tracked step when available
    const stateStep = sessionData?.current_step;
    if (stateStep === 'complete') {
      highestIndex = stepOrder.length - 1;
    } else if (stateStep) {
      const idx = stepOrder.indexOf(stateStep);
      if (idx >= 0) highestIndex = Math.max(highestIndex, idx);
    }

    // Infer progress from available data
    if (sessionData?.council_config) {
      highestIndex = Math.max(highestIndex, stepOrder.indexOf('build'), stepOrder.indexOf('edit'));
    }
    if (sessionData?.execution_results) {
      highestIndex = Math.max(highestIndex, stepOrder.indexOf('execute'));
    }
    if (sessionData?.peer_reviews || sessionData?.chairman_verdict) {
      highestIndex = Math.max(highestIndex, stepOrder.indexOf('review'));
    }

    // Always include the current route's step
    const currentIdx = stepOrder.indexOf(getCurrentStep());
    if (currentIdx >= 0) {
      highestIndex = Math.max(highestIndex, currentIdx);
    }

    return stepOrder.slice(0, highestIndex + 1);
  };

  const handleStepSelect = (stepKey) => {
    const target = stepPaths[stepKey];
    if (target && target !== location.pathname) {
      navigate(target);
    }
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

  const sidebarKey = (base) => (sessionId ? `${base}_${sessionId}` : base);

  const readStoredVisibility = (key, fallback = true) => {
    try {
      const value = localStorage.getItem(key);
      if (value === null) return fallback;
      return value === 'true';
    } catch (err) {
      return fallback;
    }
  };

  const persistVisibility = (key, value) => {
    try {
      localStorage.setItem(key, String(value));
    } catch (err) {
      // Ignore storage failures (e.g., private mode)
    }
  };

  const readStoredWidth = (key, fallback, min, max) => {
    try {
      const value = localStorage.getItem(key);
      if (value === null) return fallback;
      const parsed = parseInt(value, 10);
      if (Number.isNaN(parsed)) return fallback;
      return Math.min(Math.max(parsed, min), max);
    } catch (err) {
      return fallback;
    }
  };

  const persistWidth = (key, value) => {
    try {
      localStorage.setItem(key, String(value));
    } catch (err) {
      // Ignore storage failures
    }
  };

  const updateVisibility = useCallback((width = window.innerWidth) => {
    const canShowLeft = width >= LEFT_BREAKPOINT;
    const canShowRight = width >= RIGHT_BREAKPOINT;
    setLeftVisible(canShowLeft && leftPrefRef.current);
    setRightVisible(canShowRight && rightPrefRef.current);
  }, []);

  const toggleLeftSidebar = () => {
    const next = !leftPrefRef.current;
    leftPrefRef.current = next;
    persistVisibility(sidebarKey(LEFT_SIDEBAR_KEY), next);
    updateVisibility();
  };

  const toggleRightSidebar = () => {
    const next = !rightPrefRef.current;
    rightPrefRef.current = next;
    persistVisibility(sidebarKey(RIGHT_SIDEBAR_KEY), next);
    updateVisibility();
  };

  const setBodyDragging = (active) => {
    try {
      document.body.style.userSelect = active ? 'none' : '';
      document.body.style.cursor = active ? 'col-resize' : '';
    } catch (err) {
      // ignore
    }
  };

  // Dragging for resizable panes
  useEffect(() => {
    const handleMouseMove = (e) => {
      const { side, startX, startWidth } = dragStateRef.current;
      if (!side) return;
      const delta = e.clientX - startX;
      if (side === 'left') {
        const nextWidth = Math.min(Math.max(startWidth + delta, MIN_LEFT_WIDTH), MAX_LEFT_WIDTH);
        setLeftWidth(nextWidth);
      }
      if (side === 'right') {
        const nextWidth = Math.min(Math.max(startWidth - delta, MIN_RIGHT_WIDTH), MAX_RIGHT_WIDTH);
        setRightWidth(nextWidth);
      }
    };

    const handleMouseUp = () => {
      const { side } = dragStateRef.current;
      if (side === 'left') {
        persistWidth(sidebarKey(LEFT_WIDTH_KEY), leftWidth);
      } else if (side === 'right') {
        persistWidth(sidebarKey(RIGHT_WIDTH_KEY), rightWidth);
      }
      dragStateRef.current = { side: null, startX: 0, startWidth: 0 };
      setBodyDragging(false);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [leftWidth, rightWidth, sessionId]);

  const startDrag = (side, startX) => {
    setBodyDragging(true);
    if (side === 'left') {
      dragStateRef.current = { side, startX, startWidth: leftWidth };
    } else if (side === 'right') {
      dragStateRef.current = { side, startX, startWidth: rightWidth };
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
  
  // Initialize sidebar visibility + widths + responsive collapse
  useEffect(() => {
    const init = () => {
      const storedLeft = readStoredVisibility(sidebarKey(LEFT_SIDEBAR_KEY), true);
      const storedRight = readStoredVisibility(sidebarKey(RIGHT_SIDEBAR_KEY), true);
      const storedLeftWidth = readStoredWidth(
        sidebarKey(LEFT_WIDTH_KEY),
        300,
        MIN_LEFT_WIDTH,
        MAX_LEFT_WIDTH
      );
      const storedRightWidth = readStoredWidth(
        sidebarKey(RIGHT_WIDTH_KEY),
        320,
        MIN_RIGHT_WIDTH,
        MAX_RIGHT_WIDTH
      );
      leftPrefRef.current = storedLeft;
      rightPrefRef.current = storedRight;
      setLeftWidth(storedLeftWidth);
      setRightWidth(storedRightWidth);
      updateVisibility();
    };

    init();
    const handleResize = () => updateVisibility();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [updateVisibility, sessionId]);

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
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
      <Stepper
        currentStep={getCurrentStep()}
        allowedSteps={computeAllowedSteps()}
        onStepSelect={handleStepSelect}
      />

      <div className="relative flex-1 flex min-w-0 min-h-0 overflow-hidden">
        {/* Left toggle tab (mirrored) */}
        <button
          type="button"
          onClick={toggleLeftSidebar}
          className="fixed left-3 top-24 z-20 inline-flex items-center justify-center h-10 w-9 rounded-r-full bg-white border border-gray-200 shadow-md hover:bg-gray-50 transition-colors translate-x-1"
          aria-label={leftVisible ? 'Hide left sidebar' : 'Show left sidebar'}
        >
          {leftVisible ? (
            <ChevronLeft className="h-4 w-4 text-gray-700" />
          ) : (
            <ChevronRight className="h-4 w-4 text-gray-700" />
          )}
        </button>

        {/* Right toggle tab */}
        <button
          type="button"
          onClick={toggleRightSidebar}
          className="fixed right-3 top-24 z-20 inline-flex items-center justify-center h-10 w-9 rounded-l-full bg-white border border-gray-200 shadow-md hover:bg-gray-50 transition-colors -translate-x-1"
          aria-label={rightVisible ? 'Hide right sidebar' : 'Show right sidebar'}
        >
          {rightVisible ? (
            <ChevronRight className="h-4 w-4 text-gray-700" />
          ) : (
            <ChevronLeft className="h-4 w-4 text-gray-700" />
          )}
        </button>

        {/* Left Sidebar - User's Sessions */}
        {leftVisible && (
          <div
            className="relative flex-shrink-0 h-full bg-gray-50 border-r border-gray-200"
            style={{ width: leftWidth }}
          >
            <UserSessionsSidebar
              toggleLeftSidebar={toggleLeftSidebar}
              leftVisible={leftVisible}
            />
            <div
              className="absolute top-0 right-0 h-full w-3 cursor-col-resize hover:bg-primary-100/70 z-10"
              onMouseDown={(e) => {
                e.preventDefault();
                startDrag('left', e.clientX);
              }}
            />
          </div>
        )}
        
        {/* Main Content */}
        <main className="flex-1 overflow-y-auto min-w-0">
          <Outlet context={contextValue} />
        </main>
        
        {/* Right Sidebar - Current Session Details */}
        {sessionData && rightVisible && (
          <div
            className="relative flex-shrink-0 h-full bg-gray-50 border-l border-gray-200"
            style={{ width: rightWidth }}
          >
            <SessionSidebar session={sessionData} tokens={tokens} />
            <div
              className="absolute top-0 left-0 h-full w-3 cursor-col-resize hover:bg-primary-100/70 z-10"
              onMouseDown={(e) => {
                e.preventDefault();
                startDrag('right', e.clientX);
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};
