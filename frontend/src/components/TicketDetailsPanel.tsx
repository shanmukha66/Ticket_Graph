import { X, ExternalLink, Tag, Calendar, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';

interface TicketDetailsPanelProps {
  ticket: {
    id: string;
    project?: string;
    status?: string;
    priority?: string;
    summary?: string;
    text?: string;
    communityId?: number;
    score?: number;
  } | null;
  onClose: () => void;
}

export function TicketDetailsPanel({ ticket, onClose }: TicketDetailsPanelProps) {
  if (!ticket) return null;

  const priorityColors: Record<string, string> = {
    'Critical': 'bg-red-100 text-red-800 border-red-300',
    'Blocker': 'bg-red-100 text-red-800 border-red-300',
    'Major': 'bg-orange-100 text-orange-800 border-orange-300',
    'Minor': 'bg-yellow-100 text-yellow-800 border-yellow-300',
    'Trivial': 'bg-gray-100 text-gray-800 border-gray-300',
  };

  const statusColors: Record<string, string> = {
    'Open': 'bg-blue-100 text-blue-800 border-blue-300',
    'In Progress': 'bg-purple-100 text-purple-800 border-purple-300',
    'Resolved': 'bg-green-100 text-green-800 border-green-300',
    'Closed': 'bg-gray-100 text-gray-800 border-gray-300',
  };

  return (
    <div className="fixed right-4 top-20 bottom-4 w-96 bg-white rounded-xl shadow-2xl border border-gray-200 flex flex-col z-50 animate-slide-in-right">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-blue-600 rounded-lg">
            <Tag className="h-4 w-4 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Ticket Details</h3>
            <p className="text-sm text-gray-600">#{ticket.id}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 hover:bg-white rounded-lg transition-colors"
          aria-label="Close"
        >
          <X className="h-5 w-5 text-gray-500" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Metadata */}
        <div className="grid grid-cols-2 gap-3">
          {ticket.project && (
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="text-xs text-gray-500 mb-1">Project</div>
              <div className="font-semibold text-gray-900">{ticket.project}</div>
            </div>
          )}

          {ticket.status && (
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="text-xs text-gray-500 mb-1">Status</div>
              <span className={cn(
                "inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border",
                statusColors[ticket.status] || 'bg-gray-100 text-gray-800 border-gray-300'
              )}>
                {ticket.status}
              </span>
            </div>
          )}

          {ticket.priority && (
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="text-xs text-gray-500 mb-1">Priority</div>
              <span className={cn(
                "inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border",
                priorityColors[ticket.priority] || 'bg-gray-100 text-gray-800 border-gray-300'
              )}>
                <AlertCircle className="h-3 w-3 mr-1" />
                {ticket.priority}
              </span>
            </div>
          )}

          {ticket.communityId !== undefined && ticket.communityId !== null && (
            <div className="p-3 bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg border border-purple-200">
              <div className="text-xs text-purple-600 mb-1">Cluster</div>
              <div className="font-semibold text-purple-900">#{ticket.communityId}</div>
            </div>
          )}
        </div>

        {/* Relevance Score */}
        {ticket.score !== undefined && (
          <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-green-900">Relevance Score</span>
              <span className="text-xl font-bold text-green-700">
                {(ticket.score * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-green-200 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${ticket.score * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Summary */}
        {ticket.summary && (
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
              <span className="w-1 h-4 bg-blue-600 rounded-full"></span>
              Summary
            </h4>
            <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg border border-gray-200">
              {ticket.summary}
            </p>
          </div>
        )}

        {/* Full Text/Description */}
        {ticket.text && (
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
              <span className="w-1 h-4 bg-indigo-600 rounded-full"></span>
              Full Description
            </h4>
            <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg border border-gray-200 max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap font-sans">
                {ticket.text.length > 1000 
                  ? ticket.text.substring(0, 1000) + '...' 
                  : ticket.text}
              </pre>
            </div>
          </div>
        )}

        {/* View in Database Link */}
        <button
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all shadow-md hover:shadow-lg"
          onClick={() => {
            console.log('View ticket in database:', ticket.id);
            // You could open Neo4j Browser or external link here
          }}
        >
          <ExternalLink className="h-4 w-4" />
          View in Neo4j Browser
        </button>
      </div>
    </div>
  );
}

