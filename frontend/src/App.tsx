import { Network, Sparkles } from 'lucide-react';
import { Toast, useToast } from './components/ui/toast';
import ClusterComparison from './components/ClusterComparison';

function App() {
  const { toasts, showToast, removeToast } = useToast();

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

      {/* Main Content: Cluster comparison dashboard */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <ClusterComparison />
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
