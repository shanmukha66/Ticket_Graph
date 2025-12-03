import React, { useState } from 'react';
import { Search, Clock, Target, Zap, Award, TrendingUp } from 'lucide-react';
import { searchTickets, type ClusterSearchResponse } from '../lib/api';

interface ClusterComparisonProps {
  // Optional props for customization
}

const ClusterComparison: React.FC<ClusterComparisonProps> = () => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<ClusterSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<'smart' | 'manual' | 'single'>('single');
  const [selectedClusters, setSelectedClusters] = useState<('A' | 'B' | 'C')[]>(['A', 'B', 'C']);
  const [selectedClusterType, setSelectedClusterType] = useState<'A' | 'B' | 'C'>('A');

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    if (mode === 'manual' && selectedClusters.length === 0) {
      setError('Please select at least one cluster type (A, B, or C)');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      let clusterTypes: ('A' | 'B' | 'C')[] | undefined;
      if (mode === 'single') {
        clusterTypes = [selectedClusterType];
      } else if (mode === 'manual') {
        clusterTypes = selectedClusters;
      }

      const data = await searchTickets(query.trim(), 10, {
        use_smart_routing: mode === 'smart',
        apply_feedback_boost: true,
        cluster_types: clusterTypes,
      });
      setResults(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Search failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  // Determine badges for each cluster type
  const getBadges = (clusterType: string, allResults: ClusterSearchResponse['results']) => {
    const badges: string[] = [];
    const results = Object.values(allResults).filter(Boolean);
    
    // Badges only make sense when there is something to compare.
    // If we have fewer than 2 cluster types, skip all badges to avoid
    // misleading labels like "Fastest" when only one cluster is present.
    if (results.length < 2) return badges;

    // Find fastest
    const fastest = results.reduce((prev, curr) => 
      curr.latency_ms < prev.latency_ms ? curr : prev
    );
    if (allResults[`cluster_type_${clusterType}`]?.latency_ms === fastest.latency_ms) {
      badges.push('Fastest');
    }

    // Find best quality (highest avg similarity)
    const bestQuality = results.reduce((prev, curr) =>
      curr.avg_similarity > prev.avg_similarity ? curr : prev
    );
    if (allResults[`cluster_type_${clusterType}`]?.avg_similarity === bestQuality.avg_similarity) {
      badges.push('Best Quality');
    }

    // Find most efficient (lowest candidates scanned with good similarity)
    const mostEfficient = results.reduce((prev, curr) => {
      const prevEfficiency = curr.avg_similarity / (prev.num_candidates_scanned || 1);
      const currEfficiency = curr.avg_similarity / (curr.num_candidates_scanned || 1);
      return currEfficiency > prevEfficiency ? curr : prev;
    });
    if (allResults[`cluster_type_${clusterType}`]?.num_candidates_scanned === mostEfficient.num_candidates_scanned) {
      badges.push('Most Efficient');
    }

    return badges;
  };

  const getClusterLabel = (type: string) => {
    switch (type) {
      case 'a':
        return 'Cluster Type A (K-Means, ~100 tickets/cluster)';
      case 'b':
        return 'Cluster Type B (DBSCAN, ~500 tickets/cluster)';
      case 'c':
        return 'Cluster Type C (Agglomerative, ~1000 tickets/cluster)';
      default:
        return `Cluster Type ${type.toUpperCase()}`;
    }
  };

  const getClusterColor = (type: string) => {
    switch (type) {
      case 'a':
        return 'border-red-300 bg-red-50';
      case 'b':
        return 'border-yellow-300 bg-yellow-50';
      case 'c':
        return 'border-green-300 bg-green-50';
      default:
        return 'border-gray-300 bg-gray-50';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Cluster Comparison Search
          </h1>
          <p className="text-gray-600">
            Compare search results across three clustering strategies
          </p>
        </div>

        {/* Search + Mode Selection */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8 space-y-4">
          {/* Mode toggle */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-gray-700">Search mode:</span>
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="radio"
                  name="routing-mode"
                  value="single"
                  checked={mode === 'single'}
                  onChange={() => setMode('single')}
                  className="h-4 w-4 text-blue-600"
                />
                <span>Single Cluster Type</span>
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="radio"
                  name="routing-mode"
                  value="smart"
                  checked={mode === 'smart'}
                  onChange={() => setMode('smart')}
                  className="h-4 w-4 text-blue-600"
                />
                <span>Smart (auto-select)</span>
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="radio"
                  name="routing-mode"
                  value="manual"
                  checked={mode === 'manual'}
                  onChange={() => setMode('manual')}
                  className="h-4 w-4 text-blue-600"
                />
                <span>Manual (choose multiple)</span>
              </label>
            </div>

            {mode === 'single' && (
              <div className="flex items-center gap-3 text-sm text-gray-700">
                <span className="font-medium">Cluster Type:</span>
                {(['A', 'B', 'C'] as const).map((c) => (
                  <label key={c} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="cluster-type"
                      value={c}
                      checked={selectedClusterType === c}
                      onChange={() => setSelectedClusterType(c)}
                      className="h-4 w-4 text-blue-600"
                    />
                    <span className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                      selectedClusterType === c
                        ? (c === 'A' ? 'bg-red-100 text-red-700 border-2 border-red-300'
                        : c === 'B' ? 'bg-yellow-100 text-yellow-700 border-2 border-yellow-300'
                        : 'bg-green-100 text-green-700 border-2 border-green-300')
                        : 'bg-gray-50 text-gray-600 border border-gray-200'
                    }`}>
                      {c} {c === 'A' ? '(K-Means, ~100/cluster)' : c === 'B' ? '(DBSCAN, ~500/cluster)' : '(Agglomerative, ~1000/cluster)'}
                    </span>
                  </label>
                ))}
              </div>
            )}

            {mode === 'manual' && (
              <div className="flex items-center gap-3 text-sm text-gray-700">
                <span className="font-medium">Clusters:</span>
                {(['A', 'B', 'C'] as const).map((c) => (
                  <label key={c} className="flex items-center gap-1">
                    <input
                      type="checkbox"
                      checked={selectedClusters.includes(c)}
                      onChange={() => {
                        setSelectedClusters((prev) =>
                          prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
                        );
                      }}
                      className="h-4 w-4 text-blue-600"
                    />
                    <span>{c}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-4">
            <div className="flex-1">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Enter your search query (e.g., 'login issue', 'payment error', 'database timeout')"
                className="w-full px-4 py-3 bg-white text-gray-900 placeholder:text-gray-500 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isLoading}
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={isLoading || !query.trim()}
              className="px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Searching...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Search
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Routing Info */}
        {results?.routing_info && (
          <div className="bg-blue-100 border border-blue-300 rounded-xl p-4 mb-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-blue-500 rounded-lg">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-blue-900 mb-1">Smart Routing Decision</h3>
                <p className="text-blue-800">{results.routing_info.explanation}</p>
                <div className="mt-2 text-sm text-blue-700">
                  <span className="font-medium">Selected clusters:</span>{' '}
                  {results.routing_info.selected_clusters.join(', ')}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Results Comparison */}
        {results && (
          <div className="space-y-6">
            {mode === 'single' ? (
              // Single cluster view - full width
              <div className="max-w-4xl mx-auto">
                {selectedClusterType === 'A' && results.results.cluster_type_a && (
                  <ClusterResultCard
                    clusterType="a"
                    label={getClusterLabel('a')}
                    result={results.results.cluster_type_a}
                    colorClass={getClusterColor('a')}
                    badges={[]}
                  />
                )}
                {selectedClusterType === 'B' && results.results.cluster_type_b && (
                  <ClusterResultCard
                    clusterType="b"
                    label={getClusterLabel('b')}
                    result={results.results.cluster_type_b}
                    colorClass={getClusterColor('b')}
                    badges={[]}
                  />
                )}
                {selectedClusterType === 'C' && results.results.cluster_type_c && (
                  <ClusterResultCard
                    clusterType="c"
                    label={getClusterLabel('c')}
                    result={results.results.cluster_type_c}
                    colorClass={getClusterColor('c')}
                    badges={[]}
                  />
                )}
              </div>
            ) : (
              // Multiple cluster comparison view
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Cluster Type A */}
                {results.results.cluster_type_a && (
                  <ClusterResultCard
                    clusterType="a"
                    label={getClusterLabel('a')}
                    result={results.results.cluster_type_a}
                    colorClass={getClusterColor('a')}
                    badges={getBadges('a', results.results)}
                  />
                )}

                {/* Cluster Type B */}
                {results.results.cluster_type_b && (
                  <ClusterResultCard
                    clusterType="b"
                    label={getClusterLabel('b')}
                    result={results.results.cluster_type_b}
                    colorClass={getClusterColor('b')}
                    badges={getBadges('b', results.results)}
                  />
                )}

                {/* Cluster Type C */}
                {results.results.cluster_type_c && (
                  <ClusterResultCard
                    clusterType="c"
                    label={getClusterLabel('c')}
                    result={results.results.cluster_type_c}
                    colorClass={getClusterColor('c')}
                    badges={getBadges('c', results.results)}
                  />
                )}
              </div>
            )}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-xl shadow-lg p-6 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

interface ClusterResultCardProps {
  clusterType: string;
  label: string;
  result: ClusterSearchResponse['results']['cluster_type_a'];
  colorClass: string;
  badges: string[];
}

const ClusterResultCard: React.FC<ClusterResultCardProps> = ({
  clusterType,
  label,
  result,
  colorClass,
  badges,
}) => {
  return (
    <div className={`bg-white rounded-xl shadow-lg border-2 ${colorClass} p-6`}>
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold text-gray-900">{label}</h2>
          {badges.length > 0 && (
            <div className="flex gap-1 flex-wrap">
              {badges.map((badge) => (
                <span
                  key={badge}
                  className="px-2 py-1 text-xs font-semibold bg-blue-600 text-white rounded"
                >
                  {badge}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Metrics */}
      <div className="space-y-3 mb-6">
        {/* Latency */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-600">
            <Clock className="w-4 h-4" />
            <span className="text-sm">Latency</span>
          </div>
          <span className="font-semibold text-gray-900">{result.latency_ms.toFixed(2)} ms</span>
        </div>

        {/* Average Similarity */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-600">
            <Target className="w-4 h-4" />
            <span className="text-sm">Avg Similarity</span>
          </div>
          <span className="font-semibold text-gray-900">
            {(result.avg_similarity * 100).toFixed(1)}%
          </span>
        </div>

        {/* Candidates Scanned */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-600">
            <TrendingUp className="w-4 h-4" />
            <span className="text-sm">Candidates Scanned</span>
          </div>
          <span className="font-semibold text-gray-900">
            {result.num_candidates_scanned.toLocaleString()}
          </span>
        </div>
      </div>

      {/* Top-K Tickets */}
      <div className="border-t border-gray-200 pt-4">
        <h3 className="font-semibold text-gray-900 mb-3">
          Top {result.top_k.length} Results
        </h3>
        <div className="space-y-3">
          {result.top_k.map((ticket, index) => (
            <div
              key={ticket.ticket_id}
              className="bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-start justify-between mb-1">
                <span className="text-xs font-mono text-gray-500">{ticket.ticket_id}</span>
                <span className="text-xs font-semibold text-blue-600">
                  {(ticket.similarity * 100).toFixed(1)}%
                </span>
              </div>
              <h4 className="font-medium text-gray-900 mb-1 line-clamp-2">{ticket.title}</h4>
              <div className="flex items-center justify-between mt-1">
                <span className="text-xs text-gray-500">
                  Rank #{index + 1}
                </span>
                <span className="text-xs font-semibold text-blue-600">
                  {(ticket.similarity * 100).toFixed(1)}% match
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ClusterComparison;

