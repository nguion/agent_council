import React from 'react';
import { Clock, DollarSign, Zap } from 'lucide-react';

export const SessionSidebar = ({ session, tokens }) => {
  if (!session) return null;
  
  const formatTokens = (num) => {
    if (!num) return '0';
    return num.toLocaleString();
  };
  
  const formatCost = (cost) => {
    if (!cost) return '$0.00';
    return `$${cost.toFixed(4)}`;
  };
  
  return (
    <div className="w-80 bg-gray-50 border-l border-gray-200 p-6 overflow-y-auto">
      <div className="space-y-6">
        {/* Session Info */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
            Session Info
          </h3>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="space-y-3">
              <div>
                <div className="text-xs font-medium text-gray-500 mb-1.5">Question:</div>
                <div className="text-sm text-gray-900 leading-snug break-words" title={session.question}>
                  {session.question.length > 120 
                    ? `${session.question.substring(0, 120)}...` 
                    : session.question}
                </div>
              </div>
              {session.council_config?.council_name && (
                <div className="pt-3 border-t border-gray-100">
                  <div className="text-xs font-medium text-gray-500 mb-1.5">Council:</div>
                  <div className="text-sm text-gray-900 font-medium break-words">{session.council_config.council_name}</div>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Token Usage */}
        {tokens && (tokens.total_tokens > 0) && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
              Usage & Cost
            </h3>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Zap className="h-4 w-4 text-gray-400 mr-2" />
                    <span className="text-sm text-gray-600">Input Tokens</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {formatTokens(tokens.input_tokens)}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Zap className="h-4 w-4 text-gray-400 mr-2" />
                    <span className="text-sm text-gray-600">Output Tokens</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {formatTokens(tokens.output_tokens)}
                  </span>
                </div>
                
                <div className="flex items-center justify-between pt-2 border-t border-gray-200">
                  <div className="flex items-center">
                    <Zap className="h-4 w-4 text-primary-600 mr-2" />
                    <span className="text-sm font-semibold text-gray-900">Total Tokens</span>
                  </div>
                  <span className="text-sm font-bold text-gray-900">
                    {formatTokens(tokens.total_tokens)}
                  </span>
                </div>
                
                <div className="flex items-center justify-between pt-2 border-t border-gray-200">
                  <div className="flex items-center">
                    <DollarSign className="h-4 w-4 text-green-600 mr-2" />
                    <span className="text-sm font-semibold text-gray-900">Total Cost</span>
                  </div>
                  <span className="text-sm font-bold text-green-600">
                    {formatCost(tokens.total_cost_usd)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Updated Time */}
        {session.updated_at && (
          <div className="text-xs text-gray-500 flex items-center">
            <Clock className="h-3 w-3 mr-1" />
            Last updated: {new Date(session.updated_at).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
};
