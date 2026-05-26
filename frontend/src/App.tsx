import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import LiveExplorer from "./pages/LiveExplorer";
import DbExplorer from "./pages/DbExplorer";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/live" element={<LiveExplorer />} />
        <Route path="/db" element={<DbExplorer />} />
      </Routes>
    </BrowserRouter>
  );
}
