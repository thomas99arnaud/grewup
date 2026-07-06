import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./shared/Layout";
import { HomePage } from "./modules/offers/HomePage";
import { OffersListPage } from "./modules/offers/OffersListPage";
import { OfferDetailPage } from "./modules/offers/OfferDetailPage";
import { AddOfferPage } from "./modules/offers/AddOfferPage";
import { ProfilePage } from "./modules/profile/ProfilePage";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="offers" element={<OffersListPage />} />
          <Route path="offers/add" element={<AddOfferPage />} />
          <Route path="offers/:id" element={<OfferDetailPage />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>
);
