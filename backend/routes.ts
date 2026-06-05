import https from "https";
import { Request, Response, Application } from "express";
import { hashParams, cacheGet, cacheSet, queryCache, CACHE_SIZE } from "./cache";
import { CT_GOV_BASE, fetchAllPages } from "./ctgov";

export function registerRoutes(app: Application): void {
  app.get("/api/trials", (req: Request, res: Response) => {
    const params = new URLSearchParams(req.query as Record<string, string>);
    const url = `${CT_GOV_BASE}?${params.toString()}`;
    console.log(`[/api/trials] ${url}`);

    https
      .get(url, { headers: { Accept: "application/json" } }, (upstream) => {
        res.setHeader("Content-Type", "application/json");
        upstream.pipe(res);
      })
      .on("error", (err) => {
        console.error("Upstream error:", err.message);
        res.status(502).json({ error: "Failed to reach ClinicalTrials.gov" });
      });
  });

  app.get("/api/trials/all", async (req: Request, res: Response) => {
    const params = new URLSearchParams(req.query as Record<string, string>);
    const hash = hashParams(params);

    const cached = await cacheGet(hash);
    if (cached) {
      console.log(`[/api/trials/all] cache hit (${queryCache.size}/${CACHE_SIZE}): ${hash}`);
      res.json(cached);
      return;
    }

    try {
      const result = await fetchAllPages(params);
      await cacheSet(hash, result);
      console.log(`[/api/trials/all] cached to disk (${queryCache.size}/${CACHE_SIZE}): ${hash}`);
      res.json(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      console.error("[/api/trials/all] error:", message);
      res.status(502).json({ error: "Failed to fetch all pages from ClinicalTrials.gov" });
    }
  });

  app.get("/debug/memory", (_req, res) => {
    const m = process.memoryUsage();
    const mb = (n: number) => `${(n / 1024 / 1024).toFixed(1)} MB`;
    res.json({
      heapUsed:     mb(m.heapUsed),
      heapTotal:    mb(m.heapTotal),
      rss:          mb(m.rss),
      external:     mb(m.external),
      cacheEntries: queryCache.size,
    });
  });
}
