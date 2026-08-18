  import { NavLink, Outlet } from "react-router-dom"

  function Layout() {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <h1>Internship Tracker</h1>
        <nav>
          <NavLink
              to="/dashboard"
              className={({ isActive }) => 
                  isActive ? "nav-link active" : "nav-link"
              }
          >Dashboard
          </NavLink>

          <NavLink
              to="/analytics"
              className={({ isActive }) => 
                  isActive ? "nav-link active" : "nav-link"
              }
          >
              Analytics
          </NavLink>

          <NavLink
              to="/calendar"
              className={({ isActive }) => 
                  isActive ? "nav-link active" : "nav-link"
              }
          >
              Calendar
          </NavLink>
        </nav>
      </aside>

      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout;