import React, { useState } from 'react';
import { Search, TrendingUp, Clock, Target, Award } from 'lucide-react';

interface BenchmarkResult {
  latency_ms: number;
  nodes_scanned: number;
  avg_similarity: number;
  num_results: number;
  ticket_ids: string[];
}

interface BenchmarkResponse {
  query: string;
  results: {
    clusterA: BenchmarkResult;
    clusterB: BenchmarkResult;
    clusterC: BenchmarkResult;
  };
  best_cluster: string;
}

const ClusterBenchmark: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<BenchmarkResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleBenchmark = async () => {
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://127.0.0.1:8001/benchmark/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query.trim(), top_k: 10 }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: BenchmarkResponse = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run benchmark');
    } finally {
      setLoading(false);
    }
  };

  const getClusterColor = (clusterType: string) => {
    switch (clusterType) {
      case 'A':
        return 'bg-red-500';
      case 'B':
        return 'bg-yellow-500';
      case 'C':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getClusterLabel = (clusterType: string) => {
    switch (clusterType) {
      case 'A':
        return 'Cluster A (Coarse)';
      case 'B':
        return 'Cluster B (Medium)';
      case 'C':
        return 'Cluster C (Fine-grained)';
      default:
        return clusterType;
    }
  };

  const formatLatency = (ms: number) => {
    return `${ms.toFixed(2)} ms`;
  };

  const formatSimilarity = (sim: number) => {
    return (sim * 100).toFixed(1) + '%';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-indigo-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            Cluster Performance Benchmark
          </h1>
          <p className="text-gray-300">
            Compare query performance across three clustering strategies
          </p>
        </div>

        {/* Query Input */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 mb-8 shadow-xl">
          <div className="flex gap-4">
            <div className="flex-1">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleBenchmark()}
                placeholder="Enter your query (e.g., 'login issue', 'payment error', 'performance problem')"
                className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-gray-300 border border-white/30 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={handleBenchmark}
              disabled={loading}
              className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Running...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Benchmark
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Results */}
        {results && (
          <div className="space-y-6">
            {/* Best Cluster Badge */}
            <div className="bg-gradient-to-r from-green-500/20 to-blue-500/20 backdrop-blur-lg rounded-xl p-6 border border-green-500/30">
              <div className="flex items-center gap-3">
                <Award className="w-8 h-8 text-yellow-400" />
                <div>
                  <h3 className="text-xl font-bold text-white">
                    Best Performing Cluster: {getClusterLabel(results.best_cluster)}
                  </h3>
                  <p className="text-gray-300">
                    Optimal balance of speed and accuracy for this query
                  </p>
                </div>
              </div>
            </div>

            {/* Cluster Comparison Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {(['A', 'B', 'C'] as const).map((clusterType) => {
                const result = results.results[`cluster${clusterType}` as keyof typeof results.results];
                const isBest = results.best_cluster === clusterType;

                return (
                  <div
                    key={clusterType}
                    className={`bg-white/10 backdrop-blur-lg rounded-xl p-6 shadow-xl border-2 ${
                      isBest
                        ? 'border-yellow-400 shadow-yellow-400/20'
                        : 'border-white/20'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-4 h-4 rounded-full ${getClusterColor(clusterType)}`}
                        />
                        <h3 className="text-xl font-bold text-white">
                          {getClusterLabel(clusterType)}
                        </h3>
                      </div>
                      {isBest && (
                        <Award className="w-6 h-6 text-yellow-400" />
                      )}
                    </div>

                    <div className="space-y-4">
                      {/* Latency */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-gray-300">
                          <Clock className="w-4 h-4" />
                          <span>Latency</span>
                        </div>
                        <span className="text-white font-semibold">
                          {formatLatency(result.latency_ms)}
                        </span>
                      </div>

                      {/* Similarity */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-gray-300">
                          <Target className="w-4 h-4" />
                          <span>Similarity</span>
                        </div>
                        <span className="text-white font-semibold">
                          {formatSimilarity(result.avg_similarity)}
                        </span>
                      </div>

                      {/* Nodes Scanned */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-gray-300">
                          <TrendingUp className="w-4 h-4" />
                          <span>Nodes Scanned</span>
                        </div>
                        <span className="text-white font-semibold">
                          {result.nodes_scanned.toLocaleString()}
                        </span>
                      </div>

                      {/* Results Count */}
                      <div className="flex items-center justify-between">
                        <span className="text-gray-300">Results</span>
                        <span className="text-white font-semibold">
                          {result.num_results}
                        </span>
                      </div>

                      {/* Similarity Bar */}
                      <div className="mt-4">
                        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${getClusterColor(clusterType)} transition-all duration-500`}
                            style={{ width: `${result.avg_similarity * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Ticket IDs */}
                    {result.ticket_ids.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-white/20">
                        <p className="text-sm text-gray-400 mb-2">Top Results:</p>
                        <div className="flex flex-wrap gap-1">
                          {result.ticket_ids.slice(0, 5).map((id) => (
                            <span
                              key={id}
                              className="px-2 py-1 bg-white/10 rounded text-xs text-gray-300"
                            >
                              {id}
                            </span>
                          ))}
                          {result.ticket_ids.length > 5 && (
                            <span className="px-2 py-1 text-xs text-gray-400">
                              +{result.ticket_ids.length - 5} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Performance Comparison Chart */}
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 shadow-xl">
              <h3 className="text-xl font-bold text-white mb-4">
                Performance Comparison
              </h3>
              <div className="space-y-4">
                {/* Latency Comparison */}
                <div>
                  <p className="text-gray-300 mb-2">Query Latency (lower is better)</p>
                  <div className="flex items-center gap-4">
                    {(['A', 'B', 'C'] as const).map((clusterType) => {
                      const result = results.results[`cluster${clusterType}` as keyof typeof results.results];
                      const maxLatency = Math.max(
                        results.results.clusterA.latency_ms,
                        results.results.clusterB.latency_ms,
                        results.results.clusterC.latency_ms
                      );
                      const width = (result.latency_ms / maxLatency) * 100;

                      return (
                        <div key={clusterType} className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm text-gray-300">
                              {clusterType}
                            </span>
                            <span className="text-sm text-white font-semibold">
                              {formatLatency(result.latency_ms)}
                            </span>
                          </div>
                          <div className="h-4 bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${getClusterColor(clusterType)} transition-all duration-500`}
                              style={{ width: `${width}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Similarity Comparison */}
                <div>
                  <p className="text-gray-300 mb-2">Average Similarity (higher is better)</p>
                  <div className="flex items-center gap-4">
                    {(['A', 'B', 'C'] as const).map((clusterType) => {
                      const result = results.results[`cluster${clusterType}` as keyof typeof results.results];
                      const width = result.avg_similarity * 100;

                      return (
                        <div key={clusterType} className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm text-gray-300">
                              {clusterType}
                            </span>
                            <span className="text-sm text-white font-semibold">
                              {formatSimilarity(result.avg_similarity)}
                            </span>
                          </div>
                          <div className="h-4 bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${getClusterColor(clusterType)} transition-all duration-500`}
                              style={{ width: `${width}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClusterBenchmark;



