import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Workflow, CheckCircle2, Clock, AlertCircle, Users, FileText, TrendingUp, Bell, MessageSquare } from 'lucide-react';

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  states: number;
  avgCompletionTime: string;
  usageCount: number;
}

interface ActiveWorkflow {
  id: string;
  templateName: string;
  contentTitle: string;
  currentState: string;
  assignee: string;
  startedAt: string;
  status: 'active' | 'completed' | 'stalled' | 'pending-approval';
  studentName?: string;
  priority?: 'low' | 'medium' | 'high';
  notes?: string;
  draftContent?: string;
}

export function WorkflowTemplates() {
  // Load workflows from localStorage or use defaults
  const loadWorkflows = (): ActiveWorkflow[] => {
    const saved = localStorage.getItem('eduhub-workflows');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse saved workflows:', e);
      }
    }
    
    // Default workflows
    return [
      {
        id: 'w1',
        templateName: 'Course Add/Drop Request',
        contentTitle: 'Add Advanced Database Systems',
        currentState: 'Pending Admin Approval',
        assignee: 'Academic Advisor',
        startedAt: '1 hour ago',
        status: 'pending-approval',
        studentName: 'student@example.com',
        priority: 'high'
      },
      {
        id: 'w2',
        templateName: 'Course Approval Workflow',
        contentTitle: 'Introduction to Machine Learning',
        currentState: 'Department Review',
        assignee: 'Dr. Smith',
        startedAt: '2 days ago',
        status: 'active'
      },
      {
        id: 'w3',
        templateName: 'Content Review Process',
        contentTitle: 'Physics Lab Manual Update',
        currentState: 'Peer Review',
        assignee: 'Prof. Johnson',
        startedAt: '1 day ago',
        status: 'active'
      },
      {
        id: 'w4',
        templateName: 'Student Project Submission',
        contentTitle: 'Senior Thesis - Biology',
        currentState: 'Final Approval',
        assignee: 'Committee',
        startedAt: '5 days ago',
        status: 'stalled'
      }
    ];
  };

  const [activeTab, setActiveTab] = useState<'templates' | 'active' | 'history'>('templates');
  const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null);
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<ActiveWorkflow | null>(null);
  const [showWorkflowDetails, setShowWorkflowDetails] = useState(false);
  const [activeWorkflows, setActiveWorkflows] = useState<ActiveWorkflow[]>(loadWorkflows());
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [showDraftModal, setShowDraftModal] = useState(false);
  const [tempNotes, setTempNotes] = useState('');
  const [tempDraft, setTempDraft] = useState('');

  useEffect(() => {
    fetchTemplates();
  }, []);

  // Save workflows to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('eduhub-workflows', JSON.stringify(activeWorkflows));
  }, [activeWorkflows]);

  const fetchTemplates = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/workflows/templates', {
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch workflow templates');
      }
      
      const data = await response.json();
      
      // Transform API response to match our interface
      const transformedTemplates = data.templates.map((t: any) => ({
        id: t.id,
        name: t.name,
        description: t.description,
        category: t.category || 'General',
        states: t.states?.length || 0,
        avgCompletionTime: '3-5 days', // Mock for now
        usageCount: Math.floor(Math.random() * 200) + 50 // Mock for now
      }));
      
      setTemplates(transformedTemplates);
    } catch (err) {
      // Don't show error - just use mock data for demo
      console.log('Using mock workflow templates for demo');
      // Fall back to mock data for demo
      const mockTemplates: WorkflowTemplate[] = [
    {
      id: '1',
      name: 'Course Approval Workflow',
      description: 'Multi-step approval process for new course proposals',
      category: 'Academic',
      states: 5,
      avgCompletionTime: '3-5 days',
      usageCount: 156
    },
    {
      id: '2',
      name: 'Content Review Process',
      description: 'Peer review workflow for educational content',
      category: 'Content',
      states: 4,
      avgCompletionTime: '1-2 days',
      usageCount: 89
    },
    {
      id: '3',
      name: 'Student Project Submission',
      description: 'Workflow for student project submission and grading',
      category: 'Academic',
      states: 6,
      avgCompletionTime: '5-7 days',
      usageCount: 234
    },
    {
      id: '4',
      name: 'Resource Request',
      description: 'Request and approval workflow for educational resources',
      category: 'Administrative',
      states: 3,
      avgCompletionTime: '1-3 days',
      usageCount: 67
    }
  ];
      setTemplates(mockTemplates);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyTemplate = (template: WorkflowTemplate) => {
    setSelectedTemplate(template);
    setShowApplyModal(true);
  };

  const renderTemplates = () => {
    if (loading) {
      return (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (error) {
      return (
        <Card className="border-red-200 bg-red-50">
          <div className="text-red-700">
            <span className="font-medium">Error:</span> {error}
          </div>
        </Card>
      );
    }

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">Available Templates</h2>
          <select className="px-3 py-2 border border-gray-300 rounded-md text-sm">
            <option>All Categories</option>
            <option>Academic</option>
            <option>Content</option>
            <option>Administrative</option>
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((template) => (
          <Card key={template.id} className="hover:shadow-lg transition-shadow">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <Workflow className="h-6 w-6 text-blue-600" />
                </div>
                <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full">
                  {template.category}
                </span>
              </div>
              
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{template.name}</h3>
              <p className="text-sm text-gray-600 mb-4">{template.description}</p>
              
              <div className="space-y-2 mb-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">States:</span>
                  <span className="font-medium">{template.states}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Avg. Time:</span>
                  <span className="font-medium">{template.avgCompletionTime}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Used:</span>
                  <span className="font-medium">{template.usageCount} times</span>
                </div>
              </div>
              
              <button
                onClick={() => handleApplyTemplate(template)}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                Apply Template
              </button>
            </div>
          </Card>
        ))}
        </div>
      </div>
    );
  };

  const renderActiveWorkflows = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Active Workflows</h2>
        <div className="flex gap-2">
          <button className="px-3 py-1 text-sm bg-gray-100 rounded-md hover:bg-gray-200">
            All Status
          </button>
          <button className="px-3 py-1 text-sm bg-gray-100 rounded-md hover:bg-gray-200">
            My Workflows
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Content
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Template
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current State
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Assignee
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Started
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {activeWorkflows.map((workflow) => (
                <tr 
                  key={workflow.id} 
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => {
                    setSelectedWorkflow(workflow);
                    setShowWorkflowDetails(true);
                  }}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    <div className="flex items-center gap-2">
                      <span className="text-blue-600 hover:text-blue-800 hover:underline">
                        {workflow.contentTitle}
                      </span>
                      {workflow.notes && (
                        <MessageSquare className="h-4 w-4 text-gray-400" title="Has notes" />
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {workflow.templateName}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {workflow.currentState}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {workflow.assignee}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {workflow.startedAt}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        workflow.status === 'active' ? 'bg-green-100 text-green-800' :
                        workflow.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                        workflow.status === 'pending-approval' ? 'bg-purple-100 text-purple-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {workflow.status === 'active' && <CheckCircle2 className="h-3 w-3 mr-1" />}
                        {workflow.status === 'stalled' && <AlertCircle className="h-3 w-3 mr-1" />}
                        {workflow.status === 'pending-approval' && <Bell className="h-3 w-3 mr-1" />}
                        {workflow.status.replace('-', ' ')}
                      </span>
                      {workflow.priority === 'high' && (
                        <span className="text-xs text-red-600 font-medium">High Priority</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 border-2 border-purple-200 bg-purple-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-purple-700 font-medium">Pending Approvals</p>
              <p className="text-2xl font-bold text-purple-900">
                {activeWorkflows.filter(w => w.status === 'pending-approval').length}
              </p>
              <p className="text-xs text-purple-600 mt-1">Student requests</p>
            </div>
            <Bell className="h-8 w-8 text-purple-600" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Workflows</p>
              <p className="text-2xl font-bold text-gray-900">
                {activeWorkflows.filter(w => w.status === 'active').length}
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Awaiting Action</p>
              <p className="text-2xl font-bold text-gray-900">
                {activeWorkflows.filter(w => w.status === 'stalled').length}
              </p>
            </div>
            <Clock className="h-8 w-8 text-yellow-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Completed Today</p>
              <p className="text-2xl font-bold text-gray-900">
                {activeWorkflows.filter(w => w.status === 'completed').length}
              </p>
            </div>
            <CheckCircle2 className="h-8 w-8 text-blue-500" />
          </div>
        </Card>
      </div>
    </div>
  );

  const renderHistory = () => (
    <div className="space-y-6">
      <Card className="p-8 text-center">
        <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Workflow History</h3>
        <p className="text-gray-600 mb-4">
          View completed workflows and audit trails
        </p>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
          Coming Soon
        </button>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Workflow Templates</h1>
        <p className="mt-2 text-gray-600">
          Manage approval workflows and track content through various stages.
        </p>
      </div>

      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('templates')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'templates'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Templates
          </button>
          <button
            onClick={() => setActiveTab('active')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'active'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Active Workflows
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'history'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            History
          </button>
        </nav>
      </div>

      <div className="py-6">
        {activeTab === 'templates' && renderTemplates()}
        {activeTab === 'active' && renderActiveWorkflows()}
        {activeTab === 'history' && renderHistory()}
      </div>

      {/* Apply Template Modal */}
      {showApplyModal && selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Apply {selectedTemplate.name}</h3>
            <p className="text-gray-600 mb-4">
              Select content to apply this workflow template to:
            </p>
            <select id="content-select" className="w-full px-3 py-2 border border-gray-300 rounded-md mb-4">
              <option>Select content...</option>
              <option>Introduction to Python Programming</option>
              <option>Advanced Chemistry Lab Manual</option>
              <option>History Department Curriculum Update</option>
              <option>New Course: Machine Learning Basics</option>
              <option>Student Handbook 2025 Edition</option>
            </select>
            <div className="flex gap-2">
              <button
                onClick={() => setShowApplyModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  // Get selected content from dropdown
                  const selectElement = document.getElementById('content-select') as HTMLSelectElement;
                  const selectedContent = selectElement?.value;
                  
                  // Validate selection
                  if (!selectedContent || selectedContent === 'Select content...') {
                    alert('Please select content to apply the workflow to.');
                    return;
                  }
                  
                  // Create new workflow entry
                  const newWorkflow: ActiveWorkflow = {
                    id: `w${Date.now()}`,
                    templateName: selectedTemplate.name,
                    contentTitle: selectedContent,
                    currentState: 'Draft',
                    assignee: 'admin@example.com',
                    startedAt: 'Just now',
                    status: 'active',
                    priority: 'medium'
                  };
                  
                  // Add to active workflows
                  setActiveWorkflows(prev => [newWorkflow, ...prev]);
                  
                  // Close modal and switch to active tab
                  setShowApplyModal(false);
                  setActiveTab('active');
                }}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Apply Workflow
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Workflow Details Modal */}
      {showWorkflowDetails && selectedWorkflow && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">{selectedWorkflow.contentTitle}</h3>
                <p className="text-sm text-gray-600 mt-1">Workflow ID: {selectedWorkflow.id}</p>
              </div>
              <button
                onClick={() => setShowWorkflowDetails(false)}
                className="text-gray-500 hover:text-gray-700 p-2 rounded-md hover:bg-gray-100 transition-colors border border-gray-300"
                title="Close"
                style={{ position: 'relative', zIndex: 100 }}
              >
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-6">
              {/* Workflow Information */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Workflow Information</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Template:</span>
                    <p className="font-medium">{selectedWorkflow.templateName}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Current State:</span>
                    <p className="font-medium">{selectedWorkflow.currentState}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Assigned To:</span>
                    <p className="font-medium">{selectedWorkflow.assignee}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Started:</span>
                    <p className="font-medium">{selectedWorkflow.startedAt}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Status:</span>
                    <p className="font-medium">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        selectedWorkflow.status === 'active' ? 'bg-green-100 text-green-800' :
                        selectedWorkflow.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                        selectedWorkflow.status === 'pending-approval' ? 'bg-purple-100 text-purple-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {selectedWorkflow.status.replace('-', ' ')}
                      </span>
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500">Priority:</span>
                    <p className="font-medium capitalize">{selectedWorkflow.priority || 'medium'}</p>
                  </div>
                </div>
              </div>

              {/* Workflow States */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">Workflow States</h4>
                <div className="space-y-2">
                  {['Draft', 'Initial Review', 'Department Review', 'Final Approval', 'Published'].map((state, index) => {
                    const isRejected = selectedWorkflow.currentState === 'Rejected';
                    const states = ['Draft', 'Initial Review', 'Department Review', 'Final Approval', 'Published'];
                    const currentIndex = states.indexOf(selectedWorkflow.currentState);
                    
                    return (
                      <div key={state} className="flex items-center">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                          state === selectedWorkflow.currentState 
                            ? 'bg-blue-600 text-white' 
                            : isRejected 
                            ? 'bg-gray-200 text-gray-500'
                            : index < currentIndex
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-200 text-gray-500'
                        }`}>
                          {index + 1}
                        </div>
                        <div className="ml-3 flex-1">
                          <p className={`text-sm font-medium ${
                            state === selectedWorkflow.currentState ? 'text-blue-600' : 'text-gray-900'
                          }`}>
                            {state}
                          </p>
                        </div>
                        {state === selectedWorkflow.currentState && (
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">Current</span>
                        )}
                      </div>
                    );
                  })}
                  
                  {selectedWorkflow.currentState === 'Rejected' && (
                    <div className="flex items-center">
                      <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium bg-red-600 text-white">
                        X
                      </div>
                      <div className="ml-3 flex-1">
                        <p className="text-sm font-medium text-red-600">
                          Rejected
                        </p>
                      </div>
                      <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">Current</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Content Actions */}
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Content Management</h4>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setTempNotes(selectedWorkflow.notes || '');
                      setShowNotesModal(true);
                    }}
                    className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm flex items-center gap-2"
                  >
                    <MessageSquare className="h-4 w-4" />
                    Notes & Comments
                    {selectedWorkflow.notes && <span className="text-xs bg-gray-500 px-1 rounded">Has notes</span>}
                  </button>
                  
                  <button
                    onClick={() => {
                      setTempDraft(selectedWorkflow.draftContent || '');
                      setShowDraftModal(true);
                    }}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm flex items-center gap-2"
                  >
                    <FileText className="h-4 w-4" />
                    Draft Content
                    {selectedWorkflow.draftContent && <span className="text-xs bg-indigo-500 px-1 rounded">Has content</span>}
                  </button>
                </div>
              </div>

              {/* Actions */}
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Available Actions</h4>
                <div className="flex gap-2">
                  {selectedWorkflow.currentState !== 'Published' && selectedWorkflow.currentState !== 'Rejected' && (
                    <button 
                      onClick={() => {
                        const states = ['Draft', 'Initial Review', 'Department Review', 'Final Approval', 'Published'];
                        const currentIndex = states.indexOf(selectedWorkflow.currentState);
                        if (currentIndex < states.length - 1) {
                          const nextState = states[currentIndex + 1];
                          
                          // Update the workflow
                          setActiveWorkflows(prev => prev.map(w => 
                            w.id === selectedWorkflow.id 
                              ? { 
                                  ...w, 
                                  currentState: nextState,
                                  status: nextState === 'Published' ? 'completed' as const : w.status
                                }
                              : w
                          ));
                          
                          // Update the selected workflow
                          setSelectedWorkflow({ ...selectedWorkflow, currentState: nextState });
                          
                        }
                      }}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                    >
                      Approve & Continue
                    </button>
                  )}
                  
                  {selectedWorkflow.currentState !== 'Rejected' && selectedWorkflow.currentState !== 'Published' && (
                    <button 
                      onClick={() => {
                        // Update to rejected state
                        setActiveWorkflows(prev => prev.map(w => 
                          w.id === selectedWorkflow.id 
                            ? { ...w, currentState: 'Rejected', status: 'stalled' as const }
                            : w
                        ));
                        
                        // Update the selected workflow to show the rejected state
                        setSelectedWorkflow({ ...selectedWorkflow, currentState: 'Rejected', status: 'stalled' });
                      }}
                      className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
                    >
                      Reject
                    </button>
                  )}
                  
                  {(selectedWorkflow.currentState === 'Published' || selectedWorkflow.currentState === 'Rejected') && (
                    <span className="px-4 py-2 text-sm text-gray-500 italic">
                      Workflow {selectedWorkflow.currentState === 'Published' ? 'completed' : 'terminated'}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Notes Modal */}
      {showNotesModal && selectedWorkflow && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-semibold">Notes & Comments</h3>
              <button
                onClick={() => setShowNotesModal(false)}
                className="text-gray-400 hover:text-gray-600 p-1 rounded-md hover:bg-gray-100"
                title="Close"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={8}
              placeholder="Add notes or comments about this workflow..."
              value={tempNotes}
              onChange={(e) => setTempNotes(e.target.value)}
            />
            
            <div className="flex gap-2 mt-4">
              <button
                onClick={() => setShowNotesModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  // Update the workflow
                  setActiveWorkflows(prev => prev.map(w => 
                    w.id === selectedWorkflow.id 
                      ? { ...w, notes: tempNotes }
                      : w
                  ));
                  
                  // Update the selected workflow
                  setSelectedWorkflow({ ...selectedWorkflow, notes: tempNotes });
                  
                  // Close modal
                  setShowNotesModal(false);
                }}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Save Notes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Draft Content Modal */}
      {showDraftModal && selectedWorkflow && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-semibold">Draft Content</h3>
              <button
                onClick={() => setShowDraftModal(false)}
                className="text-gray-400 hover:text-gray-600 p-1 rounded-md hover:bg-gray-100"
                title="Close"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="mb-2">
              <p className="text-sm text-gray-600">
                Edit the actual content for this workflow item. This could be the course description, 
                document text, or any other content that needs approval.
              </p>
            </div>
            
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              rows={12}
              placeholder="Enter the draft content here..."
              value={tempDraft}
              onChange={(e) => setTempDraft(e.target.value)}
            />
            
            <div className="flex gap-2 mt-4">
              <button
                onClick={() => setShowDraftModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  // Update the workflow
                  setActiveWorkflows(prev => prev.map(w => 
                    w.id === selectedWorkflow.id 
                      ? { ...w, draftContent: tempDraft }
                      : w
                  ));
                  
                  // Update the selected workflow
                  setSelectedWorkflow({ ...selectedWorkflow, draftContent: tempDraft });
                  
                  // Close modal
                  setShowDraftModal(false);
                }}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Save Draft
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}