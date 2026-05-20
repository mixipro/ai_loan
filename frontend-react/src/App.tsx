// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { FormPage } from "@/pages/FormPage";
import { ResultsPage } from "@/pages/ResultsPage";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background text-foreground">
        <Routes>
          <Route path="/" element={<Navigate to="/form" replace />} />
          <Route path="/form" element={<FormPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="*" element={<Navigate to="/form" replace />} />
        </Routes>
        <Toaster richColors position="top-right" />
      </div>
    </BrowserRouter>
  );
}

export default App;
