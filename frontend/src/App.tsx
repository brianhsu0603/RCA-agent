import { Route, Routes } from "react-router-dom";
import RCADetail from "./pages/RCADetail";
import TriageQueue from "./pages/TriageQueue";

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>RCA &amp; Triage Agent</h1>
        <p className="subtitle">Manufacturing line failure diagnosis</p>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<TriageQueue />} />
          <Route path="/rca/:runId" element={<RCADetail />} />
        </Routes>
      </main>
    </div>
  );
}
