import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "@/components/layout/Layout";
import { EscrituraDetail } from "@/pages/EscrituraDetail";
import { EscriturasPage } from "@/pages/EscriturasPage";
import { LiquidacionPage } from "@/pages/LiquidacionPage";
import { LoginPage } from "@/pages/LoginPage";
import { ConfiguracionPage } from "@/pages/ConfiguracionPage";
import { SalariosPage } from "@/pages/SalariosPage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/escrituras" replace />} />
          <Route path="/escrituras" element={<EscriturasPage />} />
          <Route path="/escrituras/:id" element={<EscrituraDetail />} />
          <Route path="/liquidacion" element={<LiquidacionPage />} />
          <Route path="/salarios" element={<SalariosPage />} />
          <Route path="/configuracion" element={<ConfiguracionPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/escrituras" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
