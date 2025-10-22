import { Skeleton } from './ui/skeleton';

export function AnswerSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* General Answer Skeleton */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
        <div className="flex items-center gap-3 mb-4">
          <Skeleton className="h-10 w-10 rounded-lg" />
          <div className="flex-1">
            <Skeleton className="h-5 w-32 mb-2" />
            <Skeleton className="h-4 w-20" />
          </div>
        </div>
        <div className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
        </div>
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex gap-4">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-5 w-32" />
          </div>
        </div>
      </div>

      {/* Graph RAG Answer Skeleton */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl shadow-lg p-6 border border-blue-100">
        <div className="flex items-center gap-3 mb-4">
          <Skeleton className="h-10 w-10 rounded-lg" />
          <div className="flex-1">
            <Skeleton className="h-5 w-36 mb-2" />
            <Skeleton className="h-4 w-28" />
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mb-4">
          <Skeleton className="h-7 w-24 rounded-full" />
          <Skeleton className="h-7 w-28 rounded-full" />
          <Skeleton className="h-7 w-26 rounded-full" />
        </div>
        <div className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-11/12" />
          <Skeleton className="h-4 w-3/4" />
        </div>
        <div className="mt-4 pt-4 border-t border-blue-200">
          <div className="grid grid-cols-3 gap-3 mb-3">
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-full" />
          </div>
          <div className="flex flex-wrap gap-1">
            <Skeleton className="h-6 w-16 rounded" />
            <Skeleton className="h-6 w-18 rounded" />
            <Skeleton className="h-6 w-20 rounded" />
            <Skeleton className="h-6 w-16 rounded" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function GraphSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <div>
          <Skeleton className="h-6 w-40 mb-2" />
          <Skeleton className="h-4 w-60" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-8 w-8 rounded-lg" />
          <Skeleton className="h-8 w-8 rounded-lg" />
          <Skeleton className="h-8 w-8 rounded-lg" />
          <Skeleton className="h-8 w-8 rounded-lg" />
        </div>
      </div>
      
      <div className="flex gap-4">
        <Skeleton className="flex-1 h-96 rounded-xl" />
        <div className="w-64 space-y-2">
          <Skeleton className="h-6 w-32 mb-3" />
          <Skeleton className="h-20 w-full rounded-lg" />
          <Skeleton className="h-20 w-full rounded-lg" />
          <Skeleton className="h-20 w-full rounded-lg" />
        </div>
      </div>
    </div>
  );
}

export function QueryBoxSkeleton() {
  return (
    <div className="w-full max-w-4xl mx-auto">
      <Skeleton className="h-16 w-full rounded-xl" />
      <div className="mt-4 flex gap-2 justify-center">
        <Skeleton className="h-8 w-48 rounded-full" />
        <Skeleton className="h-8 w-40 rounded-full" />
        <Skeleton className="h-8 w-52 rounded-full" />
      </div>
    </div>
  );
}

