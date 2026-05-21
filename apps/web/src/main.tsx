import React from "react";
import { createRoot } from "react-dom/client";

import { AdminDashboard } from "./pages/AdminDashboard";
import { IntegrationSmokeTest } from "./pages/IntegrationSmokeTest";
import "./styles.css";

function App() {
  return (
    <main className="page">
      <AdminDashboard />
      <IntegrationSmokeTest />
    </main>
  );
}

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
