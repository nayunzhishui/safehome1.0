import React from "react";
import { createRoot } from "react-dom/client";

import { IntegrationSmokeTest } from "./pages/IntegrationSmokeTest";
import "./styles.css";

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <IntegrationSmokeTest />
  </React.StrictMode>,
);
