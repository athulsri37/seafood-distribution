interface LoadMoreProps {
  shown: number;
  total: number;
  hasMore: boolean;
  loading: boolean;
  onLoadMore: () => void;
  noun: string;
}

export default function LoadMore({ shown, total, hasMore, loading, onLoadMore, noun }: LoadMoreProps) {
  if (total === 0) return null;
  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 text-sm text-slate-500">
      <span>
        Showing {shown} of {total} {noun}
      </span>
      {hasMore && (
        <button
          type="button"
          onClick={onLoadMore}
          disabled={loading}
          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 disabled:opacity-60 rounded-md text-slate-700"
        >
          {loading ? "Loading…" : "Load more"}
        </button>
      )}
    </div>
  );
}
