import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import { UserSessionsSidebar, SessionSidebar, Stepper } from '../components';

const LEFT_SIDEBAR_KEY = 'home_left_sidebar_visible';
const RIGHT_SIDEBAR_KEY = 'home_right_sidebar_visible';
const LEFT_WIDTH_KEY = 'home_left_sidebar_width';
const RIGHT_WIDTH_KEY = 'home_right_sidebar_width';
const RIGHT_BREAKPOINT = 1200;
const LEFT_BREAKPOINT = 992;
const MIN_LEFT_WIDTH = 240;
const MAX_LEFT_WIDTH = 420;
const MIN_RIGHT_WIDTH = 240;
const MAX_RIGHT_WIDTH = 420;

export const HomeLayout = () => {
  const [leftVisible, setLeftVisible] = useState(true);
  const [rightVisible, setRightVisible] = useState(false);
  const [leftWidth, setLeftWidth] = useState(300);
  const [rightWidth, setRightWidth] = useState(320);
  const leftPrefRef = useRef(true);
  const rightPrefRef = useRef(false);
  const dragStateRef = useRef({ side: null, startX: 0, startWidth: 0 });

  const readStoredVisibility = (key, fallback = true) => {
    try {
      const value = localStorage.getItem(key);
      if (value === null) return fallback;
      return value === 'true';
    } catch (_err) {
      return fallback;
    }
  };

  const persistVisibility = (key, value) => {
    try {
      localStorage.setItem(key, String(value));
    } catch (_err) {
      // ignore
    }
  };

  const readStoredWidth = (key, fallback, min, max) => {
    try {
      const value = localStorage.getItem(key);
      if (value === null) return fallback;
      const parsed = parseInt(value, 10);
      if (Number.isNaN(parsed)) return fallback;
      return Math.min(Math.max(parsed, min), max);
    } catch (_err) {
      return fallback;
    }
  };

  const persistWidth = (key, value) => {
    try {
      localStorage.setItem(key, String(value));
    } catch (_err) {
      // ignore
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
    persistVisibility(LEFT_SIDEBAR_KEY, next);
    updateVisibility();
  };

  const toggleRightSidebar = () => {
    const next = !rightPrefRef.current;
    rightPrefRef.current = next;
    persistVisibility(RIGHT_SIDEBAR_KEY, next);
    updateVisibility();
  };

  const setBodyDragging = (active) => {
    try {
      document.body.style.userSelect = active ? 'none' : '';
      document.body.style.cursor = active ? 'col-resize' : '';
    } catch (_err) {
      // ignore
    }
  };

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
        persistWidth(LEFT_WIDTH_KEY, leftWidth);
      } else if (side === 'right') {
        persistWidth(RIGHT_WIDTH_KEY, rightWidth);
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
  }, [leftWidth, rightWidth]);

  const startDrag = (side, startX) => {
    setBodyDragging(true);
    if (side === 'left') {
      dragStateRef.current = { side, startX, startWidth: leftWidth };
    } else if (side === 'right') {
      dragStateRef.current = { side, startX, startWidth: rightWidth };
    }
  };

  useEffect(() => {
    const storedLeft = readStoredVisibility(LEFT_SIDEBAR_KEY, true);
    const storedRight = readStoredVisibility(RIGHT_SIDEBAR_KEY, false);
    const storedLeftWidth = readStoredWidth(LEFT_WIDTH_KEY, 300, MIN_LEFT_WIDTH, MAX_LEFT_WIDTH);
    const storedRightWidth = readStoredWidth(RIGHT_WIDTH_KEY, 320, MIN_RIGHT_WIDTH, MAX_RIGHT_WIDTH);
    leftPrefRef.current = storedLeft;
    rightPrefRef.current = storedRight;
    setLeftWidth(storedLeftWidth);
    setRightWidth(storedRightWidth);
    updateVisibility();

    const handleResize = () => updateVisibility();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [updateVisibility]);

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
      <Stepper currentStep="input" allowedSteps={['input']} />
      <div className="relative flex-1 flex min-w-0 min-h-0 overflow-hidden">
        {/* Left toggle tab */}
        <button
          type="button"
          onClick={toggleLeftSidebar}
          className="fixed left-3 top-24 z-20 inline-flex items-center justify-center h-10 w-9 rounded-r-full bg-white border border-gray-200 shadow-md hover:bg-gray-50 transition-colors translate-x-1"
          aria-label={leftVisible ? 'Hide left sidebar' : 'Show left sidebar'}
        >
          {leftVisible ? (
            <span className="text-gray-700 text-sm">‹</span>
          ) : (
            <span className="text-gray-700 text-sm">›</span>
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
            <span className="text-gray-700 text-sm">›</span>
          ) : (
            <span className="text-gray-700 text-sm">‹</span>
          )}
        </button>

        {/* Left Sidebar - User's Sessions */}
        {leftVisible && (
          <div
            className="relative flex-shrink-0 h-full bg-gray-50 border-r border-gray-200 min-w-0"
            style={{ width: leftWidth }}
          >
            <UserSessionsSidebar />
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
          <Outlet />
        </main>

        {/* Right Sidebar - Placeholder */}
        {rightVisible && (
          <div
            className="relative flex-shrink-0 h-full bg-gray-50 border-l border-gray-200 min-w-0"
            style={{ width: rightWidth }}
          >
            <SessionSidebar session={{ question: 'Select a session to view details' }} />
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
