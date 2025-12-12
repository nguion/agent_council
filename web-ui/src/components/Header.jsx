import React from 'react';
import { Brain } from 'lucide-react';

export const Header = () => {
  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Brain className="h-8 w-8 text-primary-600" />
            <div className="flex items-center space-x-3">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Agent Council</h1>
                {/* Deloitte Logo */}
                <div className="flex items-center mt-1">
                  <img 
                    src="https://upload.wikimedia.org/wikipedia/commons/e/ed/Logo_of_Deloitte.svg" 
                    alt="Deloitte" 
                    className="h-4"
                  />
                </div>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <span className="px-3 py-1 text-xs font-semibold bg-primary-50 text-primary-700 rounded-full border border-primary-200">
              Beta
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
