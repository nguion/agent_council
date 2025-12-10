import React, { useState } from 'react';
import { Plus, Edit2, Trash2, Copy, Search, AlertCircle } from 'lucide-react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';

export const Step3Edit = ({ initialConfig, onNext, onBack }) => {
  const [councilConfig, setCouncilConfig] = useState(initialConfig);
  const [editingAgent, setEditingAgent] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  
  const updateAgent = (index, updates) => {
    const newAgents = [...councilConfig.agents];
    newAgents[index] = { ...newAgents[index], ...updates };
    setCouncilConfig({ ...councilConfig, agents: newAgents });
  };
  
  const deleteAgent = (index) => {
    if (window.confirm('Are you sure you want to remove this agent?')) {
      const newAgents = councilConfig.agents.filter((_, i) => i !== index);
      setCouncilConfig({ ...councilConfig, agents: newAgents });
    }
  };
  
  const duplicateAgent = (index) => {
    const agent = councilConfig.agents[index];
    const newAgent = { ...agent, name: `${agent.name} (Copy)` };
    setCouncilConfig({
      ...councilConfig,
      agents: [...councilConfig.agents, newAgent]
    });
  };
  
  const addAgent = (newAgent) => {
    setCouncilConfig({
      ...councilConfig,
      agents: [...councilConfig.agents, newAgent]
    });
    setShowAddModal(false);
  };
  
  const handleContinue = () => {
    if (councilConfig.agents.length === 0) {
      if (!window.confirm('The council is empty. Are you sure you want to continue?')) {
        return;
      }
    }
    onNext(councilConfig);
  };
  
  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          Edit Your Council
        </h2>
        <p className="text-gray-600">
          Refine the agents, adjust their personas, or add new members before execution.
        </p>
        <div className="mt-4 flex items-center space-x-4">
          <span className="text-sm text-gray-500">
            {councilConfig.agents.length} agent(s)
          </span>
          {councilConfig.agents.length === 0 && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
              <AlertCircle className="h-4 w-4 mr-1" />
              Council is empty
            </span>
          )}
        </div>
      </div>
      
      {/* Agent List */}
      <div className="space-y-4 mb-8">
        {councilConfig.agents.map((agent, index) => (
          <Card key={index}>
            <div className="space-y-4">
              {/* Agent Header */}
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <input
                    type="text"
                    value={agent.name}
                    onChange={(e) => updateAgent(index, { name: e.target.value })}
                    className="text-lg font-semibold text-gray-900 border-0 border-b border-transparent hover:border-gray-300 focus:border-primary-500 focus:ring-0 px-0 w-full"
                  />
                </div>
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => setEditingAgent(editingAgent === index ? null : index)}
                    className="p-2 text-gray-400 hover:text-primary-600 rounded-lg hover:bg-gray-100"
                    title="Edit"
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => duplicateAgent(index)}
                    className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-gray-100"
                    title="Duplicate"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => deleteAgent(index)}
                    className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-gray-100"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              
              {/* Agent Settings */}
              <div className="flex items-center space-x-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={agent.enable_web_search}
                    onChange={(e) => updateAgent(index, { enable_web_search: e.target.checked })}
                    className="rounded text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700 flex items-center">
                    <Search className="h-4 w-4 mr-1" />
                    Web Search
                  </span>
                </label>
                
                <div className="flex items-center space-x-2">
                  <label className="text-sm text-gray-700">Reasoning:</label>
                  <select
                    value={agent.reasoning_effort || 'medium'}
                    onChange={(e) => updateAgent(index, { reasoning_effort: e.target.value })}
                    className="text-sm border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="none">None</option>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
              </div>
              
              {/* Persona */}
              {editingAgent === index ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Persona Description
                  </label>
                  <textarea
                    value={agent.persona}
                    onChange={(e) => updateAgent(index, { persona: e.target.value })}
                    rows={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none text-sm"
                  />
                  <Button
                    variant="secondary"
                    className="mt-2"
                    onClick={() => setEditingAgent(null)}
                  >
                    Done
                  </Button>
                </div>
              ) : (
                <div className="text-sm text-gray-600">
                  <p className="line-clamp-2">{agent.persona}</p>
                  <button
                    onClick={() => setEditingAgent(index)}
                    className="text-primary-600 hover:text-primary-700 text-xs mt-1"
                  >
                    Edit full persona →
                  </button>
                </div>
              )}
            </div>
          </Card>
        ))}
        
        {/* Add Agent Button */}
        <button
          onClick={() => setShowAddModal(true)}
          className="w-full p-6 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-primary-500 hover:text-primary-600 transition-colors flex items-center justify-center space-x-2"
        >
          <Plus className="h-5 w-5" />
          <span>Add New Agent</span>
        </button>
      </div>
      
      {/* Actions */}
      <div className="bg-white rounded-lg shadow-md border-2 border-primary-200 p-6">
        <div className="flex justify-between items-center">
          <Button variant="secondary" onClick={onBack}>
            ← Back
          </Button>
          <Button onClick={handleContinue} disabled={councilConfig.agents.length === 0}>
            Save & Execute Council →
          </Button>
        </div>
      </div>
      
      {/* Add Agent Modal */}
      {showAddModal && (
        <AddAgentModal
          onAdd={addAgent}
          onCancel={() => setShowAddModal(false)}
        />
      )}
    </div>
  );
};

const AddAgentModal = ({ onAdd, onCancel }) => {
  const [newAgent, setNewAgent] = useState({
    name: '',
    persona: '',
    enable_web_search: true,
    reasoning_effort: 'medium'
  });
  
  const handleSubmit = () => {
    if (!newAgent.name.trim() || !newAgent.persona.trim()) {
      alert('Please provide both name and persona');
      return;
    }
    onAdd(newAgent);
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-xl font-semibold text-gray-900">Add New Agent</h3>
        </div>
        
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Agent Name
            </label>
            <input
              type="text"
              value={newAgent.name}
              onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="e.g., Financial Analyst"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Persona Description
            </label>
            <textarea
              value={newAgent.persona}
              onChange={(e) => setNewAgent({ ...newAgent, persona: e.target.value })}
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              placeholder="Describe who this agent is, their expertise, perspective, and approach..."
            />
          </div>
          
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={newAgent.enable_web_search}
                onChange={(e) => setNewAgent({ ...newAgent, enable_web_search: e.target.checked })}
                className="rounded text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">Enable Web Search</span>
            </label>
            
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-700">Reasoning Effort:</label>
              <select
                value={newAgent.reasoning_effort}
                onChange={(e) => setNewAgent({ ...newAgent, reasoning_effort: e.target.value })}
                className="text-sm border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="none">None</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>
        </div>
        
        <div className="p-6 border-t border-gray-200 flex justify-end space-x-4">
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>
            Add Agent
          </Button>
        </div>
      </div>
    </div>
  );
};
