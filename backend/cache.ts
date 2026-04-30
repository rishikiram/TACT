import fs from "fs";
import path from "path";
import crypto from "crypto";

export const CACHE_SIZE = 8;
const CACHE_DIR = path.join(__dirname, "cache");

export type QueryResult = { studies: unknown[]; totalCount: number };

// LRU index: Map<hash, true> — preserves insertion order for eviction.
// Actual data lives in CACHE_DIR/{hash}.json.
export const queryCache = new Map<string, true>();

function cacheFilePath(hash: string): string {
  return path.join(CACHE_DIR, `${hash}.json`);
}

export function hashParams(params: URLSearchParams): string {
  const sorted = new URLSearchParams([...params.entries()].sort()).toString();
  return crypto.createHash("md5").update(sorted).digest("hex");
}

export async function cacheGet(hash: string): Promise<QueryResult | undefined> {
  if (!queryCache.has(hash)) return undefined;
  try {
    const raw = await fs.promises.readFile(cacheFilePath(hash), "utf8");
    queryCache.delete(hash);
    queryCache.set(hash, true);
    return JSON.parse(raw) as QueryResult;
  } catch {
    queryCache.delete(hash);
    return undefined;
  }
}

export async function cacheSet(hash: string, value: QueryResult): Promise<void> {
  if (queryCache.has(hash)) queryCache.delete(hash);
  if (queryCache.size >= CACHE_SIZE) {
    const oldest = queryCache.keys().next().value!;
    queryCache.delete(oldest);
    fs.unlink(cacheFilePath(oldest), () => {});
  }
  await fs.promises.mkdir(CACHE_DIR, { recursive: true });
  await fs.promises.writeFile(cacheFilePath(hash), JSON.stringify(value), "utf8");
  queryCache.set(hash, true);
}

export async function clearCache(): Promise<void> {
  for (const hash of queryCache.keys()) {
    await fs.promises.unlink(cacheFilePath(hash)).catch(() => {});
  }
  queryCache.clear();
}

// On startup: rebuild LRU index from disk, sorted oldest→newest by mtime
export function loadCacheFromDisk(): void {
  if (!fs.existsSync(CACHE_DIR)) return;
  const files = fs.readdirSync(CACHE_DIR).filter((f) => f.endsWith(".json"));
  const sorted = files
    .map((f) => ({ hash: f.slice(0, -5), mtime: fs.statSync(path.join(CACHE_DIR, f)).mtimeMs }))
    .sort((a, b) => a.mtime - b.mtime);

  const toDelete = sorted.slice(0, -CACHE_SIZE);
  for (const { hash } of toDelete) fs.unlink(cacheFilePath(hash), () => {});
  for (const { hash } of sorted.slice(-CACHE_SIZE)) queryCache.set(hash, true);

  if (queryCache.size > 0) {
    console.log(`[cache] loaded ${queryCache.size} entr${queryCache.size === 1 ? "y" : "ies"} from disk`);
  }
}
