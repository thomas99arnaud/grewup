import { Link, Outlet, useLocation } from "react-router-dom";

const nav = [
  { to: "/", label: "Dashboard" },
  { to: "/offers", label: "Offres" },
  { to: "/offers/add", label: "Ajouter" },
  { to: "/scrape", label: "Scraping" },
];

export function Layout() {
  const location = useLocation();

  return (
    <div className="app">
      <header className="header">
        <h1>Grew</h1>
        <nav>
          {nav.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={location.pathname === item.to ? "active" : ""}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
