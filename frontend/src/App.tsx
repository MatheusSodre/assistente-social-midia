import { Route, Routes } from "react-router-dom";
import { Layout } from "@/components/layout/Layout";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import BrandMemoryPage from "@/pages/BrandMemory";
import CreatePost from "@/pages/CreatePost";
import Dashboard from "@/pages/Dashboard";
import History from "@/pages/History";
import Login from "@/pages/Login";
import Templates from "@/pages/Templates";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="criar" element={<CreatePost />} />
          <Route path="brand-memory" element={<BrandMemoryPage />} />
          <Route path="historico" element={<History />} />
          <Route path="templates" element={<Templates />} />
        </Route>
      </Route>
    </Routes>
  );
}
