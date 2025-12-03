import React, { useState, useEffect } from 'react';
import { Play, Clock, BarChart3, TrendingUp, Database, Cpu, Layers } from 'lucide-react';
import { runClustering, getClusteringStats, type ClusteringResponse, type ClusteringStats } from '../lib/api';

interface ComparisonResult {
  subsetSize: number;
  algorithm: string;
  result: ClusteringResponse;
}

const ClusteringDemo: React.FC = () => {
  const [query, setQuery] = useState('');
  const [subsetSize, setSubsetSize] = useState<100 | 500 | 1000 | 'all'>(100);
  const [algorithm, setAlgorithm] = useState<'kmeans' | 'agglomerative' | 'dbscan' | 'all'>('kmeans');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ClusteringResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<ClusteringStats | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await getClusteringStats();
      setStats(data);
    } catch (err: any) {
      console.error('Failed to load stats:', err);
    }
  };

  const handleRunClustering = async () => {
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      // If 'all' is selected, pass null to run all combinations
      // Otherwise pass the specific values
      const data = await runClustering(
        query.trim(),
        subsetSize === 'all' ? undefined : subsetSize,
        algorithm === 'all' ? undefined : algorithm
      );
      setResult(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Clustering failed');
    } finally {
      setIsLoading(false);
    }
  };

  const getAlgorithmLabel = (alg: string) => {
    switch (alg) {
      case 'kmeans': return 'K-Means';
      case 'agglomerative': return 'Agglomerative Clustering';
      case 'dbscan': return 'DBSCAN';
      default: return alg;
    }
  };

  const getSubsetLabel = (size: number) => {
    switch (size) {
      case 100: return 'A (100 tickets)';
      case 500: return 'B (500 tickets)';
      case 1000: return 'C (1000 tickets)';
      default: return `${size} tickets`;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Ticket Clustering Analytics Demo
          </h1>
          <p className="text-gray-600">
            Select ticket subset size and clustering algorithm to analyze performance
          </p>
        </div>

        {/* Stats Banner */}
        {stats && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{stats.total_tickets.toLocaleString()}</div>
                <div className="text-sm text-gray-600">Total Tickets</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{stats.tickets_with_embeddings.toLocaleString()}</div>
                <div className="text-sm text-gray-600">Tickets with Embeddings</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{stats.top_categories.length}</div>
                <div className="text-sm text-gray-600">Categories</div>
              </div>
            </div>
          </div>
        )}

        {/* Query Input and Controls */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8 space-y-6">
          {/* Query Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Enter Search Query
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleRunClustering()}
              placeholder="e.g., 'login issue', 'database error', 'API timeout'"
              className="w-full px-4 py-3 bg-white text-gray-900 placeholder:text-gray-500 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            />
          </div>

          {/* Subset Size Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Ticket Subset Size
            </label>
            <div className="flex gap-3">
              {[
                { value: 100, label: 'A: 100 tickets' },
                { value: 500, label: 'B: 500 tickets' },
                { value: 1000, label: 'C: 1000 tickets' },
                { value: 'all', label: 'All (A, B, C)' }
              ].map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => setSubsetSize(value as any)}
                  className={`flex-1 px-4 py-3 rounded-lg font-medium transition-colors ${
                    subsetSize === value
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Algorithm Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Clustering Algorithm
            </label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { value: 'kmeans', label: 'K-Means' },
                { value: 'agglomerative', label: 'Agglomerative Clustering' },
                { value: 'dbscan', label: 'DBSCAN' },
                { value: 'all', label: 'All Algorithms' }
              ].map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => setAlgorithm(value as any)}
                  className={`px-4 py-3 rounded-lg font-medium transition-colors border-2 ${
                    algorithm === value
                      ? 'bg-blue-50 border-blue-600 text-blue-700'
                      : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Run Button */}
          <div>
            <button
              onClick={handleRunClustering}
              disabled={isLoading || !query.trim()}
              className="w-full px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Running Clustering...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Run Clustering
                </>
              )}
            </button>
            <p className="mt-2 text-sm text-gray-500 text-center">
              {subsetSize === 'all' && algorithm === 'all'
                ? 'Will run all 9 combinations: A/B/C × K-Means/Agglomerative/DBSCAN'
                : subsetSize === 'all'
                ? `Will run 3 combinations: A/B/C × ${getAlgorithmLabel(algorithm)}`
                : algorithm === 'all'
                ? `Will run 3 combinations: ${getSubsetLabel(subsetSize)} × All Algorithms`
                : `Will run: ${getSubsetLabel(subsetSize)} × ${getAlgorithmLabel(algorithm)}`}
            </p>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Results Summary */}
        {result && result.summary && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Query: "{result.query}"</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
                <div className="text-sm text-green-700 font-medium mb-1">Fastest</div>
                <div className="text-xl font-bold text-green-900">{result.summary.fastest}</div>
                <div className="text-sm text-green-600">{result.summary.fastest_time_ms.toFixed(2)} ms</div>
              </div>
              <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
                <div className="text-sm text-blue-700 font-medium mb-1">Best Quality</div>
                <div className="text-xl font-bold text-blue-900">{result.summary.best_quality}</div>
                <div className="text-sm text-blue-600">Score: {result.summary.best_quality_score.toFixed(3)}</div>
              </div>
              <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-4">
                <div className="text-sm text-purple-700 font-medium mb-1">Most Clusters</div>
                <div className="text-xl font-bold text-purple-900">{result.summary.most_clusters}</div>
                <div className="text-sm text-purple-600">{result.summary.most_clusters_count} clusters</div>
              </div>
            </div>
          </div>
        )}

        {/* Comparison Table */}
        {result && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">All 9 Combinations Comparison</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Combination</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subset</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Algorithm</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Clusters</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Computation (ms)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Query (ms)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total (ms)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Silhouette</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Size</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {[
                    ['A', 'kmeans'],
                    ['A', 'agglomerative'],
                    ['A', 'dbscan'],
                    ['B', 'kmeans'],
                    ['B', 'agglomerative'],
                    ['B', 'dbscan'],
                    ['C', 'kmeans'],
                    ['C', 'agglomerative'],
                    ['C', 'dbscan'],
                  ].map(([subset, algorithm]) => {
                    const key = `${subset}_${algorithm}`;
                    const res = result.results[key];
                    const subsetSize = subset === 'A' ? 100 : subset === 'B' ? 500 : 1000;
                    const combinationLabel = `${subset} (${subsetSize} tickets) × ${getAlgorithmLabel(algorithm)}`;
                    
                    if (!res) {
                      return (
                        <tr key={key} className="bg-gray-50">
                          <td colSpan={9} className="px-4 py-3 text-sm text-gray-500 text-center">
                            {combinationLabel} - Not available
                          </td>
                        </tr>
                      );
                    }
                    
                    return (
                      <tr key={key} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-semibold text-gray-900">
                          {combinationLabel}
                        </td>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">
                          {getSubsetLabel(subsetSize)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700">
                          {getAlgorithmLabel(algorithm)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700">
                          {res.num_clusters}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700">
                          {res.computation_time_ms.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700">
                          {res.query_time_ms.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-sm font-semibold text-gray-900">
                          {res.total_time_ms.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700">
                          {res.metrics.silhouette_score?.toFixed(3) || 'N/A'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700">
                          {res.metrics.avg_cluster_size?.toFixed(1) || 'N/A'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: 'blue' | 'green' | 'purple' | 'orange';
}

const MetricCard: React.FC<MetricCardProps> = ({ icon, label, value, color }) => {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600',
  };

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className={`inline-flex p-2 rounded-lg ${colorClasses[color]} mb-2`}>
        {icon}
      </div>
      <div className="text-sm text-gray-600 mb-1">{label}</div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
    </div>
  );
};

export default ClusteringDemo;

