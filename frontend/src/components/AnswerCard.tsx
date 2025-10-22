import { FileText, Network, CheckCircle2, Users, Database } from 'lucide-react';
import { cn } from '../lib/utils';
import type { GeneralAnswer, GraphRAGAnswer } from '../lib/api';

interface AnswerCardProps {
  general: GeneralAnswer;
  graphRag: GraphRAGAnswer;
}

export function AnswerCard({ general, graphRag }: AnswerCardProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* General Answer */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow duration-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-purple-100 rounded-lg">
            <FileText className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              General Answer
            </h3>
            <p className="text-sm text-gray-500">GPT-{general.model.includes('4') ? '4' : '3.5'}</p>
          </div>
        </div>

        <div className="prose prose-sm max-w-none">
          <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
            {general.answer}
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" />
              {general.tokens} tokens
            </span>
            <span className="px-2 py-0.5 bg-purple-50 text-purple-600 rounded-full">
              No context
            </span>
          </div>
        </div>
      </div>

      {/* Graph RAG Answer */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl shadow-lg p-6 border border-blue-100 hover:shadow-xl transition-shadow duration-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-blue-600 rounded-lg">
            <Network className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Graph-RAG Answer
            </h3>
            <p className="text-sm text-blue-600 font-medium">From your data</p>
          </div>
        </div>

        {/* Community badges */}
        <div className="flex flex-wrap gap-2 mb-4">
          {graphRag.clusters.map((cluster) => (
            <div
              key={cluster.cluster_id}
              className="inline-flex items-center gap-1.5 px-3 py-1 bg-white rounded-full border border-blue-200 shadow-sm"
            >
              <Users className="h-3 w-3 text-blue-600" />
              <span className="text-xs font-medium text-gray-700">
                Cluster #{cluster.cluster_id}
              </span>
              <span className="text-xs text-gray-500">
                ({cluster.size})
              </span>
            </div>
          ))}
        </div>

        <div className="prose prose-sm max-w-none">
          <div className="text-gray-800 whitespace-pre-wrap leading-relaxed bg-white/50 rounded-lg p-4">
            {/* Highlight ticket citations */}
            {highlightTicketCitations(graphRag.answer)}
          </div>
        </div>

        {/* Provenance info */}
        <div className="mt-4 pt-4 border-t border-blue-200">
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div className="flex items-center gap-1.5 text-gray-700">
              <Database className="h-3 w-3 text-blue-600" />
              <span className="font-medium">{graphRag.provenance.num_tickets}</span>
              <span className="text-gray-500">tickets</span>
            </div>
            <div className="flex items-center gap-1.5 text-gray-700">
              <FileText className="h-3 w-3 text-blue-600" />
              <span className="font-medium">{graphRag.provenance.num_sections}</span>
              <span className="text-gray-500">sections</span>
            </div>
            <div className="flex items-center gap-1.5 text-gray-700">
              <Users className="h-3 w-3 text-blue-600" />
              <span className="font-medium">{graphRag.provenance.num_communities}</span>
              <span className="text-gray-500">clusters</span>
            </div>
          </div>

          {/* Ticket citations */}
          <div className="mt-3 flex flex-wrap gap-1">
            {graphRag.provenance.ticket_ids.slice(0, 5).map((ticketId) => (
              <span
                key={ticketId}
                className="text-xs px-2 py-0.5 bg-blue-600 text-white rounded font-mono"
              >
                {ticketId}
              </span>
            ))}
            {graphRag.provenance.ticket_ids.length > 5 && (
              <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                +{graphRag.provenance.ticket_ids.length - 5} more
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Highlight ticket citations in the answer text
 */
function highlightTicketCitations(text: string) {
  // Match patterns like "PROJ-123", "TICKET-456", etc.
  const ticketPattern = /\b([A-Z]+-\d+)\b/g;
  
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = ticketPattern.exec(text)) !== null) {
    // Add text before match
    if (match.index > lastIndex) {
      parts.push(
        <span key={`text-${lastIndex}`}>
          {text.substring(lastIndex, match.index)}
        </span>
      );
    }

    // Add highlighted ticket
    parts.push(
      <span
        key={`ticket-${match.index}`}
        className="inline-flex items-center px-1.5 py-0.5 bg-blue-600 text-white rounded text-xs font-mono font-semibold mx-0.5"
      >
        {match[1]}
      </span>
    );

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(
      <span key={`text-${lastIndex}`}>
        {text.substring(lastIndex)}
      </span>
    );
  }

  return parts.length > 0 ? parts : text;
}

