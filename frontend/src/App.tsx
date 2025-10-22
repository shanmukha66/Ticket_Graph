import { useState } from 'react';
import { Network, Sparkles, AlertCircle } from 'lucide-react';
import { QueryBox } from './components/QueryBox';
import { AnswerCardEnhanced } from './components/AnswerCardEnhanced';
import { GraphPanel } from './components/GraphPanel';
import { AnswerSkeleton, GraphSkeleton } from './components/SkeletonLoader';
import { Toast, useToast } from './components/ui/toast';
import { ask, fetchGraph, type AskResponse, type SubgraphResponse } from './lib/api';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<AskResponse | null>(null);
  const [graphData, setGraphData] = useState<SubgraphResponse | null>(null);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  
  const { toasts, showToast, removeToast } = useToast();

  const handleSubmit = async (query: string) => {
    setIsLoading(true);
    setResults(null);
    setGraphData(null);
    setSelectedTicketId(null);

    try {
      // Fetch both answers and graph data in parallel
      const [answerData, subgraphData] = await Promise.all([
        ask({ query, model: 'gpt-4', top_k_sections: 10, num_hops: 1 }),
        fetchGraph(query, 10, 1, true),
      ]);

      setResults(answerData);
      setGraphData(subgraphData);
      showToast('Answers generated successfully!', 'success');
    } catch (err: any) {
      console.error('Error:', err);
      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        'An error occurred while processing your query';
      
      showToast(errorMessage, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTicketClick = (ticketId: string) => {
    setSelectedTicketId(ticketId);
    showToast(`Highlighting ${ticketId} in graph`, 'info');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50">
      {/* Toast notifications */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </div>

      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl shadow-lg">
                <Network className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  Graph RAG
                </h1>
                <p className="text-sm text-gray-600">
                  Knowledge Graph + Retrieval Augmented Generation
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-full border border-blue-200">
              <Sparkles className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-700">
                Powered by GPT-4 + Neo4j + E5
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Query Box */}
        <div className="mb-8">
          <QueryBox onSubmit={handleSubmit} isLoading={isLoading} />
        </div>

        {/* Results */}
        {isLoading && (
          <div className="space-y-8">
            <AnswerSkeleton />
            <GraphSkeleton />
          </div>
        )}

        {results && !isLoading && (
          <div className="space-y-8">
            {/* Answer Cards */}
            <div className="animate-fade-in">
              <AnswerCardEnhanced
                general={results.general}
                graphRag={results.graph_rag}
                onTicketClick={handleTicketClick}
              />
            </div>

            {/* Graph Panel */}
            <div className="animate-fade-in-delayed">
              <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 h-[600px]">
                <GraphPanel
                  data={graphData}
                  selectedTicketId={selectedTicketId}
                  onTicketClick={handleTicketClick}
                />
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!results && !isLoading && (
          <div className="text-center py-20">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 mb-6">
              <Network className="h-10 w-10 text-blue-600" />
            </div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-3">
              Welcome to Graph RAG
            </h2>
            <p className="text-gray-600 max-w-md mx-auto mb-6">
              Ask technical support questions and get dual answers: a general response
              and a context-aware answer powered by your knowledge graph.
            </p>

            {/* Feature highlights */}
            <div className="flex items-center justify-center gap-6 text-sm text-gray-500 flex-wrap">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                <span>E5 Embeddings</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                <span>FAISS Vector Search</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                <span>Neo4j Graph</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                <span>Community Detection</span>
              </div>
            </div>

            {/* Tips */}
            <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200 max-w-lg mx-auto text-left">
              <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                Tips for best results:
              </h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Be specific in your questions</li>
                <li>• Use technical terms when relevant</li>
                <li>• Try example queries above to get started</li>
                <li>• Click ticket citations to highlight in graph</li>
              </ul>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-6 py-6 mt-12 border-t border-gray-200">
        <div className="text-center text-sm text-gray-500">
          <p>
            Graph RAG combines knowledge graphs, vector search, and LLMs for
            enhanced question answering with provenance and citations.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
