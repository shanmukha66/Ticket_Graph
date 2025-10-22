import { useState, FormEvent } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { cn } from '../lib/utils';

interface QueryBoxProps {
  onSubmit: (query: string) => Promise<void>;
  isLoading?: boolean;
}

export function QueryBox({ onSubmit, isLoading = false }: QueryBoxProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      await onSubmit(query.trim());
    }
  };

  const exampleQueries = [
    'How to fix authentication timeout issues?',
    'Memory leak debugging strategies',
    'Database connection pool configuration',
  ];

  return (
    <div className="w-full max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a technical support question..."
            className={cn(
              "w-full pl-12 pr-32 py-4 text-lg",
              "bg-white border-2 border-gray-200",
              "rounded-xl shadow-lg",
              "focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100",
              "transition-all duration-200",
              "placeholder:text-gray-400",
              isLoading && "opacity-75 cursor-not-allowed"
            )}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className={cn(
              "absolute right-2 top-1/2 -translate-y-1/2",
              "px-6 py-2.5 rounded-lg",
              "bg-gradient-to-r from-blue-600 to-blue-700",
              "text-white font-medium",
              "hover:from-blue-700 hover:to-blue-800",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
              "transition-all duration-200",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "flex items-center gap-2"
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Searching...</span>
              </>
            ) : (
              <span>Search</span>
            )}
          </button>
        </div>
      </form>

      {/* Example queries */}
      <div className="mt-4 flex flex-wrap gap-2 justify-center">
        <span className="text-sm text-gray-500">Try:</span>
        {exampleQueries.map((example, index) => (
          <button
            key={index}
            onClick={() => setQuery(example)}
            disabled={isLoading}
            className={cn(
              "text-sm px-3 py-1 rounded-full",
              "bg-gray-100 text-gray-700",
              "hover:bg-gray-200 hover:text-gray-900",
              "transition-colors duration-150",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  );
}

