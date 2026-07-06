from pathlib import Path

LAYOUT = """import { Link, Outlet, useLocation } from "react-router-dom";

const nav = [
  { to: "/", label: "Accueil" },
  { to: "/offers", label: "Offres" },
  { to: "/profile", label: "Répertoire" },
  { to: "/offers/add", label: "Ajouter" },
];

export function Layout() {
  const { pathname } = useLocation();

  return (
    <div className="app">
      <header className="header">
        <Link to="/" className="brand">
          Grew
        </Link>
        <nav className="nav">
          {nav.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={
                pathname === item.to ||
                (item.to !== "/" && pathname.startsWith(item.to))
                  ? "active"
                  : ""
              }
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
"""

Path("frontend/src/shared/Layout.tsx").write_text(LAYOUT, encoding="utf-8", newline="\n")
print("Layout.tsx fixed")
