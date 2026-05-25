const cache = new Map<string, { data: unknown; ts: number }>()
const CACHE_TTL = 60_000 // 60 seconds

export async function cachedFetch<T>(key: string, fetcher: () => Promise<T>): Promise<T> {
  const entry = cache.get(key)
  if (entry && Date.now() - entry.ts < CACHE_TTL) {
    return entry.data as T
  }
  const data = await fetcher()
  cache.set(key, { data, ts: Date.now() })
  return data
}

export function clearCache(key?: string) {
  if (key) {
    cache.delete(key)
  } else {
    cache.clear()
  }
}
