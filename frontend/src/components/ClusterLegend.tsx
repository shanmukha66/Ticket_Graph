import { Users, Info } from 'lucide-react';
import { cn } from '../lib/utils';

interface Cluster {
  id: number;
  size: number;
  reason: string;
  color: string;
}

interface ClusterLegendProps {
  clusters: Cluster[];
  selectedCluster: number | null;
  onSelectCluster: (clusterId: number | null) => void;
}

export function ClusterLegend({ clusters, selectedCluster, onSelectCluster }: ClusterLegendProps) {
  if (clusters.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200">
      <div className="flex items-center gap-2 mb-3">
        <Users className="h-4 w-4 text-gray-600" />
        <h4 className="font-semibold text-sm text-gray-900">
          Communities ({clusters.length})
        </h4>
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {clusters.map((cluster) => (
          <button
            key={cluster.id}
            onClick={() => onSelectCluster(selectedCluster === cluster.id ? null : cluster.id)}
            className={cn(
              "w-full text-left p-2.5 rounded-lg border-2 transition-all duration-150",
              "hover:shadow-md",
              selectedCluster === cluster.id
                ? "border-blue-500 bg-blue-50 shadow-sm"
                : "border-gray-200 bg-white hover:border-gray-300"
            )}
          >
            <div className="flex items-start gap-2">
              <div
                className="w-3 h-3 rounded-full mt-0.5 flex-shrink-0 ring-2 ring-white shadow-sm"
                style={{ backgroundColor: cluster.color }}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-gray-900">
                    Cluster #{cluster.id}
                  </span>
                  <span className="text-xs text-gray-500">
                    ({cluster.size} tickets)
                  </span>
                </div>
                <p className="text-xs text-gray-600 leading-relaxed">
                  {cluster.reason}
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t border-gray-200">
        <div className="flex items-start gap-2 text-xs text-gray-500">
          <Info className="h-3 w-3 mt-0.5 flex-shrink-0" />
          <span>Click a cluster to highlight its nodes in the graph</span>
        </div>
      </div>
    </div>
  );
}

