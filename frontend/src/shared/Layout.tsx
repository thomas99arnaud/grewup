import { Link, Outlet, useLocation } from "react-router-dom";

const nav = [
  { to: "/", label: "Accueil" },
  { to: "/apply", label: "CV / lettre" },
  { to: "/applications", label: "Candidatures" },
  { to: "/offers", label: "Offres" },
  { to: "/profile", label: "Répertoire" },
  { to: "/offers/add", label: "Ajouter" },
];

function isActive(pathname: string, to: string) {
  if (to === "/") return pathname === "/";
  if (to === "/offers") {
    return (
      pathname === "/offers" ||
      (pathname.startsWith("/offers/") && !pathname.startsWith("/offers/add"))
    );
  }
  return pathname === to || pathname.startsWith(`${to}/`);
}

export function Layout() {
  const { pathname } = useLocation();

  return (
    <div className="app">
      <aside className="sidebar">
        <Link to="/" className="brand">
          <img src="/grew-logo.png" alt="Grew" className="brand-logo" />
          Grew
        </Link>
        <nav className="nav">
          {nav.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={isActive(pathname, item.to) ? "active" : ""}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
