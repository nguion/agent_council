import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Upload, X, FileText, List } from 'lucide-react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { agentCouncilAPI } from '../api';

export const Step1Input = () => {
  const navigate = useNavigate();
  const [question, setQuestion] = useState('');
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles([...files, ...droppedFiles]);
  };
  
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };
  
  const handleDragLeave = () => {
    setIsDragging(false);
  };
  
  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles([...files, ...selectedFiles]);
  };
  
  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };
  
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };
  
  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    return <FileText className="h-5 w-5 text-gray-400" />;
  };
  
  const handleSubmit = async () => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      const result = await agentCouncilAPI.createSession(question.trim(), files);
      
      // Navigate to the newly created session's build page
      navigate(`/sessions/${result.session_id}/build`);
    } catch (err) {
      console.error('Failed to create session:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to create session');
      setLoading(false);
    }
  };
  
  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          What problem do you want the council to solve?
        </h2>
        <p className="text-gray-600">
          Provide your core question and optionally add context files to help the agents understand the problem better.
        </p>
      </div>
      
      {/* Question Input */}
      <Card className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Your Question
        </label>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={4}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
          placeholder="Enter your question..."
        />
        {error && (
          <p className="mt-2 text-sm text-red-600">{error}</p>
        )}
      </Card>
      
      {/* File Upload */}
      <Card title="Add Context Files (Optional)" className="mb-6">
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragging
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-2">
            Drag and drop files here, or click to browse
          </p>
          <p className="text-sm text-gray-500 mb-4">
            Supported: PDF, DOCX, TXT, MD, JSON, PY, CSV
          </p>
          <input
            type="file"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
            accept=".pdf,.docx,.txt,.md,.json,.py,.csv"
          />
          <label htmlFor="file-upload">
            <Button variant="secondary" onClick={() => document.getElementById('file-upload').click()}>
              Browse Files
            </Button>
          </label>
        </div>
        
        {/* File List */}
        {files.length > 0 && (
          <div className="mt-6 space-y-2">
            <h4 className="text-sm font-medium text-gray-700 mb-2">
              Selected Files ({files.length})
            </h4>
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
              >
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  {getFileIcon(file.name)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="ml-4 text-gray-400 hover:text-red-600 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>
      
      {/* Action Button */}
      <div className="flex justify-center">
        <Button onClick={handleSubmit} disabled={!question.trim() || loading}>
          {loading ? 'Creating Session...' : 'Build Council'}
        </Button>
      </div>
      
      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-25 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 shadow-xl">
            <div className="animate-spin h-8 w-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto"></div>
          </div>
        </div>
      )}
    </div>
  );
};
