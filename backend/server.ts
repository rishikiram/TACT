import express from "express";
import { loadCacheFromDisk } from "./cache";
import { registerRoutes } from "./routes";

const app = express();
const PORT = 3001;

app.use(express.json());

app.use((_req, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", "http://localhost:3000");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  next();
});

loadCacheFromDisk();
registerRoutes(app);

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Backend proxy listening on http://localhost:${PORT}`);
  });
}

export default app;
