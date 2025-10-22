import { useEffect, useRef, useState } from 'react';
import cytoscape, { Core, NodeSingular } from 'cytoscape';
// @ts-ignore
import coseBilkent from 'cytoscape-cose-bilkent';
import { ZoomIn, ZoomOut, Maximize2, LayoutGrid } from 'lucide-react';
import { cn } from '../lib/utils';
import type { SubgraphResponse } from '../lib/api';
import { ClusterLegend } from './ClusterLegend';

// Register layout
cytoscape.use(coseBilkent);

interface GraphPanelProps {
  data: SubgraphResponse | null;
  isLoading?: boolean;
  selectedTicketId?: string | null;
  onTicketClick?: (ticketId: string) => void;
}

// Color palette for communities
const COMMUNITY_COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#14b8a6', // teal
  '#f97316', // orange
  '#6366f1', // indigo
  '#84cc16', // lime
];

export function GraphPanel({ data, isLoading, selectedTicketId, onTicketClick }: GraphPanelProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<number | null>(null);
  const [layout, setLayout] = useState<'cose-bilkent' | 'circle' | 'grid'>('cose-bilkent');

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      style: [
        // Ticket nodes
        {
          selector: 'node[type="Ticket"]',
          style: {
            'background-color': (ele) => {
              const commId = ele.data('communityId');
              if (commId !== undefined && commId !== null) {
                return COMMUNITY_COLORS[commId % COMMUNITY_COLORS.length];
              }
              return '#94a3b8';
            },
            'label': (ele) => {
              // Show ticket ID prominently
              const id = ele.data('id');
              return `#${id}`;
            },
            'color': '#1e293b',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '14px',
            'font-weight': 'bold',
            'text-background-color': '#ffffff',
            'text-background-opacity': 0.9,
            'text-background-padding': '4px',
            'text-background-shape': 'roundrectangle',
            'width': (ele) => {
              const degree = ele.degree();
              return Math.max(40, Math.min(80, 40 + degree * 3));
            },
            'height': (ele) => {
              const degree = ele.degree();
              return Math.max(40, Math.min(80, 40 + degree * 3));
            },
            'border-width': '3px',
            'border-color': '#ffffff',
            'border-opacity': 1,
          },
        },
        // Section nodes
        {
          selector: 'node[type="Section"]',
          style: {
            'background-color': '#e2e8f0',
            'label': '', // Hide section labels by default
            'color': '#475569',
            'font-size': '8px',
            'width': '15px',
            'height': '15px',
            'border-width': '1px',
            'border-color': '#cbd5e1',
            'opacity': 0.6,
          },
        },
        // Selected/highlighted nodes
        {
          selector: 'node.highlighted',
          style: {
            'border-width': '4px',
            'border-color': '#fbbf24',
            'z-index': 100,
          },
        },
        // Dimmed nodes (when filtering)
        {
          selector: 'node.dimmed',
          style: {
            'opacity': 0.2,
          },
        },
        // SIMILAR_TO edges
        {
          selector: 'edge[rel="SIMILAR_TO"]',
          style: {
            'width': (ele) => {
              const score = ele.data('score') || 0.5;
              return Math.max(1, score * 4);
            },
            'line-color': '#94a3b8',
            'target-arrow-color': '#94a3b8',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'opacity': 0.6,
          },
        },
        // HAS_SECTION edges
        {
          selector: 'edge[rel="HAS_SECTION"]',
          style: {
            'width': '1px',
            'line-color': '#cbd5e1',
            'line-style': 'dashed',
            'curve-style': 'bezier',
            'opacity': 0.3,
          },
        },
        // Highlighted edges
        {
          selector: 'edge.highlighted',
          style: {
            'width': '3px',
            'opacity': 1,
            'z-index': 100,
          },
        },
        // Dimmed edges
        {
          selector: 'edge.dimmed',
          style: {
            'opacity': 0.1,
          },
        },
      ],
      layout: {
        name: 'preset',
      },
    });

    // Add tooltip on hover
    cy.on('mouseover', 'node', (event) => {
      const node = event.target;
      const type = node.data('type');
      
      if (type === 'Ticket') {
        const id = node.data('id');
        const project = node.data('project') || 'Unknown';
        const status = node.data('status') || 'Unknown';
        const priority = node.data('priority') || 'Unknown';
        const score = node.data('score') || 0;
        const commId = node.data('communityId');
        
        // Create rich tooltip
        let tooltipText = `🎫 Ticket #${id}\n`;
        tooltipText += `📁 Project: ${project}\n`;
        tooltipText += `📊 Status: ${status}\n`;
        tooltipText += `⚡ Priority: ${priority}\n`;
        tooltipText += `🎯 Relevance: ${(score * 100).toFixed(1)}%`;
        
        if (commId !== undefined && commId !== null) {
          tooltipText += `\n\n🔵 Cluster #${commId}`;
          if (data?.metadata.communities) {
            const comm = data.metadata.communities.find(c => c.id === commId);
            if (comm) {
              tooltipText += `\n${comm.reason}`;
              tooltipText += `\n(${comm.size} tickets in cluster)`;
            }
          }
        }
        
        // Show tooltip as title attribute
        node.data('tooltip', tooltipText);
        console.log(tooltipText); // Also log to console for debugging
      } else if (type === 'Section') {
        const key = node.data('key');
        const text = node.data('text') || '';
        node.data('tooltip', `📄 Section: ${key}\n${text.substring(0, 100)}...`);
      }
    });

    // Highlight connected nodes on click
    cy.on('tap', 'node', (event) => {
      const node = event.target;
      const neighbors = node.neighborhood();
      
      cy.elements().removeClass('highlighted');
      node.addClass('highlighted');
      neighbors.addClass('highlighted');
      
      // If it's a ticket node, trigger callback
      if (node.data('type') === 'Ticket' && onTicketClick) {
        onTicketClick(node.data('id'));
      }
      
      // Log info to console for debugging
      if (node.data('type') === 'Ticket') {
        console.log('Ticket Details:', {
          id: node.data('id'),
          project: node.data('project'),
          status: node.data('status'),
          priority: node.data('priority'),
          communityId: node.data('communityId'),
          score: node.data('score'),
          connections: node.degree()
        });
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, []);

  // Update graph data
  useEffect(() => {
    if (!cyRef.current || !data) return;

    const cy = cyRef.current;

    // Clear existing elements
    cy.elements().remove();

    // Add new elements
    if (data.nodes.length > 0) {
      cy.add(data.nodes);
      cy.add(data.edges);

      // Run layout
      cy.layout({
        name: layout,
        animate: true,
        animationDuration: 500,
        fit: true,
        padding: 50,
        // cose-bilkent specific options
        ...(layout === 'cose-bilkent' && {
          idealEdgeLength: 100,
          nodeRepulsion: 4500,
          randomize: false,
        }),
      }).run();
    }
  }, [data, layout]);

  // Handle cluster filtering
  useEffect(() => {
    if (!cyRef.current) return;

    const cy = cyRef.current;

    if (selectedCluster === null) {
      // Show all nodes
      cy.elements().removeClass('dimmed highlighted');
    } else {
      // Dim nodes not in selected cluster
      cy.nodes().forEach((node) => {
        const commId = node.data('communityId');
        if (commId === selectedCluster) {
          node.removeClass('dimmed').addClass('highlighted');
          // Highlight connected edges
          node.connectedEdges().removeClass('dimmed').addClass('highlighted');
        } else {
          node.addClass('dimmed').removeClass('highlighted');
        }
      });

      // Dim edges not connected to highlighted nodes
      cy.edges().forEach((edge) => {
        const source = edge.source();
        const target = edge.target();
        if (source.data('communityId') !== selectedCluster && 
            target.data('communityId') !== selectedCluster) {
          edge.addClass('dimmed').removeClass('highlighted');
        }
      });
    }
  }, [selectedCluster]);

  // Handle selected ticket highlighting
  useEffect(() => {
    if (!cyRef.current || !selectedTicketId) return;

    const cy = cyRef.current;

    // Find and highlight the selected ticket
    cy.nodes().forEach((node) => {
      if (node.data('type') === 'Ticket' && node.data('id') === selectedTicketId) {
        // Center on the node
        cy.animate({
          center: { eles: node },
          zoom: 1.5,
        }, {
          duration: 500,
        });

        // Highlight the node and its neighbors
        cy.elements().removeClass('highlighted');
        node.addClass('highlighted');
        node.neighborhood().addClass('highlighted');
      }
    });
  }, [selectedTicketId]);

  // Control functions
  const handleZoomIn = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 1.2);
    }
  };

  const handleZoomOut = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 0.8);
    }
  };

  const handleFit = () => {
    if (cyRef.current) {
      cyRef.current.fit(undefined, 50);
    }
  };

  const handleLayoutChange = () => {
    const layouts: Array<'cose-bilkent' | 'circle' | 'grid'> = ['cose-bilkent', 'circle', 'grid'];
    const currentIndex = layouts.indexOf(layout);
    const nextLayout = layouts[(currentIndex + 1) % layouts.length];
    setLayout(nextLayout);
  };

  // Prepare clusters for legend
  const clusters = data?.metadata.communities.map(comm => ({
    id: comm.id,
    size: comm.size,
    reason: comm.reason,
    color: COMMUNITY_COLORS[comm.id % COMMUNITY_COLORS.length],
  })) || [];

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header with controls */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Knowledge Graph</h3>
          <p className="text-sm text-gray-500">
            {data ? `${data.metadata.num_tickets} tickets, ${data.metadata.num_edges} connections` : 'Waiting for query...'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleLayoutChange}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title={`Layout: ${layout}`}
          >
            <LayoutGrid className="h-4 w-4 text-gray-600" />
          </button>
          <button
            onClick={handleZoomIn}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title="Zoom in"
          >
            <ZoomIn className="h-4 w-4 text-gray-600" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title="Zoom out"
          >
            <ZoomOut className="h-4 w-4 text-gray-600" />
          </button>
          <button
            onClick={handleFit}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title="Fit to screen"
          >
            <Maximize2 className="h-4 w-4 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Graph container with legend */}
      <div className="flex-1 flex gap-4 min-h-[450px]">
        <div className="flex-1 bg-gray-50 rounded-xl border-2 border-gray-200 shadow-inner relative overflow-hidden min-h-[450px]">
          {isLoading && (
            <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-50">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
                <p className="mt-3 text-sm text-gray-600">Loading graph...</p>
              </div>
            </div>
          )}

          <div ref={containerRef} className="w-full h-full min-h-[450px]" />

          {!data && !isLoading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center text-gray-400">
                <div className="text-4xl mb-2">🔍</div>
                <p>Submit a query to see the knowledge graph</p>
              </div>
            </div>
          )}
        </div>

        {/* Legend */}
        {clusters.length > 0 && (
          <div className="w-64 flex-shrink-0">
            <ClusterLegend
              clusters={clusters}
              selectedCluster={selectedCluster}
              onSelectCluster={setSelectedCluster}
            />
          </div>
        )}
      </div>
    </div>
  );
}

