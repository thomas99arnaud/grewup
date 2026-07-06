import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./shared/Layout";
import { DashboardPage } from "./modules/offers/DashboardPage";
import { OffersListPage } from "./modules/offers/OffersListPage";
import { OfferDetailPage } from "./modules/offers/OfferDetailPage";
import { AddOfferPage } from "./modules/offers/AddOfferPage";
import { ScrapePage } from "./modules/offers/ScrapePage";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="offers" element={<OffersListPage />} />
          <Route path="offers/add" element={<AddOfferPage />} />
          <Route path="offers/:id" element={<OfferDetailPage />} />
          <Route path="scrape" element={<ScrapePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>
);
