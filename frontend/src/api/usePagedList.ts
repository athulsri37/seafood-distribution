import { useCallback, useEffect, useState } from "react";
import client, { errorMessage } from "./client";

interface Identified {
  id: number;
}

/**
 * A newest-first list the API pages with a cursor (`before_id`) and an X-Total-Count header.
 *
 * Changes made on the page update the loaded rows in place (`replace`, `prepend`) instead
 * of reloading, so items the user already loaded with "Load more" stay on screen.
 */
export function usePagedList<T extends Identified>(url: string, loadErrorMessage: string) {
  const [items, setItems] = useState<T[] | null>(null);
  const [total, setTotal] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");

  const fetchPage = useCallback(
    async (beforeId?: number) => {
      const res = await client.get<T[]>(url, { params: beforeId ? { before_id: beforeId } : {} });
      setTotal(Number(res.headers["x-total-count"] ?? res.data.length));
      return res.data;
    },
    [url],
  );

  const reload = useCallback(async () => {
    try {
      setItems(await fetchPage());
      setError("");
    } catch (err) {
      setError(errorMessage(err, loadErrorMessage));
    }
  }, [fetchPage, loadErrorMessage]);

  useEffect(() => {
    reload();
  }, [reload]);

  const loadMore = async () => {
    if (!items?.length) return;
    setLoadingMore(true);
    try {
      const next = await fetchPage(items[items.length - 1].id);
      setItems((current) => [...(current ?? []), ...next]);
      setError("");
    } catch (err) {
      setError(errorMessage(err, loadErrorMessage));
    } finally {
      setLoadingMore(false);
    }
  };

  const replace = (updated: T) =>
    setItems((current) => current?.map((item) => (item.id === updated.id ? updated : item)) ?? null);

  const prepend = (created: T) => {
    setItems((current) => [created, ...(current ?? [])]);
    setTotal((count) => count + 1);
  };

  return {
    items,
    total,
    hasMore: items !== null && items.length < total,
    loadingMore,
    error,
    reload,
    loadMore,
    replace,
    prepend,
  };
}
