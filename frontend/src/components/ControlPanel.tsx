import { useState } from 'react'
import { Plus, Link, Trash2, Network } from 'lucide-react'
import { graphAPI } from '../lib/api'

interface ControlPanelProps {
  onRefresh: () => void
}

const ControlPanel = ({ onRefresh }: ControlPanelProps) => {
  const [showNodeForm, setShowNodeForm] = useState(false)
  const [showRelForm, setShowRelForm] = useState(false)
  const [nodeLabel, setNodeLabel] = useState('')
  const [nodeName, setNodeName] = useState('')
  const [fromNode, setFromNode] = useState('')
  const [toNode, setToNode] = useState('')
  const [relType, setRelType] = useState('')

  const handleCreateNode = async () => {
    if (!nodeLabel || !nodeName) return

    try {
      await graphAPI.createNode(nodeLabel, { name: nodeName })
      setNodeLabel('')
      setNodeName('')
      setShowNodeForm(false)
      onRefresh()
    } catch (error) {
      console.error('Failed to create node:', error)
    }
  }

  const handleCreateRelationship = async () => {
    if (!fromNode || !toNode || !relType) return

    try {
      await graphAPI.createRelationship(fromNode, toNode, relType)
      setFromNode('')
      setToNode('')
      setRelType('')
      setShowRelForm(false)
      onRefresh()
    } catch (error) {
      console.error('Failed to create relationship:', error)
    }
  }

  const handleDetectCommunities = async () => {
    try {
      const result = await graphAPI.detectCommunities('louvain')
      alert(`Found ${result.num_communities} communities using ${result.algorithm}`)
      onRefresh()
    } catch (error) {
      console.error('Failed to detect communities:', error)
    }
  }

  const handleClearGraph = async () => {
    if (!confirm('Are you sure you want to clear the entire graph?')) return

    try {
      await graphAPI.clearGraph()
      onRefresh()
    } catch (error) {
      console.error('Failed to clear graph:', error)
    }
  }

  return (
    <div className="p-4 space-y-4">
      <h3 className="text-sm font-semibold text-gray-900">Graph Controls</h3>

      {/* Create Node */}
      <div>
        <button
          onClick={() => setShowNodeForm(!showNodeForm)}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Create Node
        </button>

        {showNodeForm && (
          <div className="mt-2 space-y-2">
            <input
              type="text"
              value={nodeLabel}
              onChange={(e) => setNodeLabel(e.target.value)}
              placeholder="Label (e.g., Person)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            <input
              type="text"
              value={nodeName}
              onChange={(e) => setNodeName(e.target.value)}
              placeholder="Name"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            <button
              onClick={handleCreateNode}
              className="w-full px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
            >
              Create
            </button>
          </div>
        )}
      </div>

      {/* Create Relationship */}
      <div>
        <button
          onClick={() => setShowRelForm(!showRelForm)}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
        >
          <Link className="h-4 w-4" />
          Create Relationship
        </button>

        {showRelForm && (
          <div className="mt-2 space-y-2">
            <input
              type="text"
              value={fromNode}
              onChange={(e) => setFromNode(e.target.value)}
              placeholder="From Node ID"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <input
              type="text"
              value={toNode}
              onChange={(e) => setToNode(e.target.value)}
              placeholder="To Node ID"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <input
              type="text"
              value={relType}
              onChange={(e) => setRelType(e.target.value)}
              placeholder="Type (e.g., KNOWS)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <button
              onClick={handleCreateRelationship}
              className="w-full px-4 py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600"
            >
              Create
            </button>
          </div>
        )}
      </div>

      {/* Community Detection */}
      <button
        onClick={handleDetectCommunities}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
      >
        <Network className="h-4 w-4" />
        Detect Communities
      </button>

      {/* Clear Graph */}
      <button
        onClick={handleClearGraph}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
      >
        <Trash2 className="h-4 w-4" />
        Clear Graph
      </button>
    </div>
  )
}

export default ControlPanel

