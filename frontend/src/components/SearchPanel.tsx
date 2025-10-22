import { useState } from 'react'
import { Search } from 'lucide-react'
import { searchAPI } from '../lib/api'
import { SearchResult } from '../types'

interface SearchPanelProps {
  onNodeSelect: (nodeId: string) => void
}

const SearchPanel = ({ onNodeSelect }: SearchPanelProps) => {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) return

    setLoading(true)
    try {
      const response = await searchAPI.search(query, 5)
      setResults(response.results)
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <div className="p-4 border-b border-gray-200">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Semantic Search</h3>
      
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Search with E5 embeddings..."
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
      </div>

      <button
        onClick={handleSearch}
        disabled={loading || !query.trim()}
        className="w-full mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? 'Searching...' : 'Search'}
      </button>

      {results.length > 0 && (
        <div className="mt-4 space-y-2">
          <h4 className="text-xs font-semibold text-gray-700 uppercase">Results</h4>
          {results.map((result) => (
            <div
              key={result.id}
              onClick={() => onNodeSelect(result.id)}
              className="p-3 bg-gray-50 rounded-md hover:bg-gray-100 cursor-pointer transition-colors"
            >
              <div className="flex justify-between items-start mb-1">
                <span className="text-sm font-medium text-gray-900">
                  {result.metadata.name || `Result ${result.id}`}
                </span>
                <span className="text-xs text-gray-500">
                  {(result.score * 100).toFixed(1)}%
                </span>
              </div>
              <p className="text-xs text-gray-600 line-clamp-2">{result.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default SearchPanel

