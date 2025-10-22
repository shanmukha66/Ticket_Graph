import { useEffect, useRef } from 'react'
import cytoscape, { Core, ElementDefinition } from 'cytoscape'
// @ts-ignore
import coseBilkent from 'cytoscape-cose-bilkent'
import { GraphData } from '../types'

cytoscape.use(coseBilkent)

interface GraphVisualizationProps {
  data: GraphData
  selectedNode: string | null
  onNodeClick: (nodeId: string) => void
}

const GraphVisualization = ({ data, selectedNode, onNodeClick }: GraphVisualizationProps) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    // Initialize Cytoscape
    const cy = cytoscape({
      container: containerRef.current,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#3b82f6',
            'label': 'data(label)',
            'color': '#fff',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '12px',
            'width': '40px',
            'height': '40px',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'background-color': '#ef4444',
            'border-width': '3px',
            'border-color': '#991b1b',
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#94a3b8',
            'target-arrow-color': '#94a3b8',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(type)',
            'font-size': '10px',
            'text-rotation': 'autorotate',
            'text-margin-y': -10,
          },
        },
      ],
      layout: {
        name: 'cose-bilkent',
        animate: true,
        animationDuration: 1000,
        fit: true,
        padding: 50,
      },
    })

    // Add click handler
    cy.on('tap', 'node', (event) => {
      const nodeId = event.target.id()
      onNodeClick(nodeId)
    })

    cyRef.current = cy

    return () => {
      cy.destroy()
    }
  }, [onNodeClick])

  useEffect(() => {
    if (!cyRef.current) return

    const cy = cyRef.current

    // Convert data to Cytoscape format
    const elements: ElementDefinition[] = [
      ...data.nodes.map((node) => ({
        data: {
          id: node.id,
          label: node.properties.name || node.label || `Node ${node.id}`,
          ...node.properties,
        },
      })),
      ...data.relationships.map((rel) => ({
        data: {
          id: rel.id,
          source: rel.from_node,
          target: rel.to_node,
          type: rel.type,
          ...rel.properties,
        },
      })),
    ]

    // Update graph
    cy.elements().remove()
    cy.add(elements)

    // Run layout
    cy.layout({
      name: 'cose-bilkent',
      animate: true,
      animationDuration: 1000,
      fit: true,
      padding: 50,
    }).run()
  }, [data])

  useEffect(() => {
    if (!cyRef.current) return

    const cy = cyRef.current

    // Update selection
    cy.nodes().removeClass('selected')
    if (selectedNode) {
      cy.getElementById(selectedNode).addClass('selected')
    }
  }, [selectedNode])

  return (
    <div className="w-full h-full relative">
      <div ref={containerRef} className="w-full h-full" />
      {data.nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <p className="text-gray-500 text-lg">No graph data to display</p>
            <p className="text-gray-400 text-sm mt-2">
              Create nodes and relationships to get started
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default GraphVisualization

