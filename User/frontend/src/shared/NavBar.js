import React, { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NavBar = () => {
  const { user, isAdmin, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="nav-bar">
      <div className="container-fluid">
        <nav className="navbar navbar-expand-lg bg-dark navbar-dark">
          <Link to="/" className="navbar-brand">
            MENU
          </Link>
          <button
            type="button"
            className="navbar-toggler"
            onClick={() => setMenuOpen((o) => !o)}
            aria-expanded={menuOpen}
            aria-label="Toggle navigation"
          >
            <span className="navbar-toggler-icon" />
          </button>

          <div
            className={`collapse navbar-collapse justify-content-between ${menuOpen ? 'show' : ''}`}
            id="navbarCollapse"
          >
            <div className="navbar-nav mr-auto">
              <NavLink end to="/" className="nav-item nav-link" onClick={() => setMenuOpen(false)}>
                Home
              </NavLink>
              <NavLink to="/about" className="nav-item nav-link" onClick={() => setMenuOpen(false)}>
                About
              </NavLink>
              <NavLink to="/service" className="nav-item nav-link" onClick={() => setMenuOpen(false)}>
                Service
              </NavLink>
              <NavLink to="/team" className="nav-item nav-link" onClick={() => setMenuOpen(false)}>
                Team
              </NavLink>
              <NavLink to="/portfolio" className="nav-item nav-link" onClick={() => setMenuOpen(false)}>
                Project
              </NavLink>
              <div className="nav-item dropdown">
                <a href="#pages" className="nav-link dropdown-toggle" data-toggle="dropdown">
                  Pages
                </a>
                <div className="dropdown-menu">
                  <NavLink to="/blog" className="dropdown-item" onClick={() => setMenuOpen(false)}>
                    Blog Page
                  </NavLink>
                  <NavLink to="/single" className="dropdown-item" onClick={() => setMenuOpen(false)}>
                    Single Page
                  </NavLink>
                </div>
              </div>
              <NavLink to="/contact" className="nav-item nav-link" onClick={() => setMenuOpen(false)}>
                Contact
              </NavLink>
              {user && (
                <NavLink to="/jobs" className="nav-item nav-link" onClick={() => setMenuOpen(false)}>
                  Jobs
                </NavLink>
              )}
            </div>
            <div className="ml-auto d-flex align-items-center gap-2">
              {user ? (
                <>
                  <NavLink to="/profile" className="nav-item nav-link" onClick={() => setMenuOpen(false)}>
                    Profile
                  </NavLink>
                  {isAdmin && (
                    <Link to="/admin" className="nav-item nav-link" onClick={() => setMenuOpen(false)}>
                      Admin
                    </Link>
                  )}
                  <button
                    type="button"
                    className="btn btn-outline-light btn-sm"
                    onClick={() => { logout(); setMenuOpen(false); }}
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" className="btn btn-outline-light btn-sm">
                    Sign In
                  </Link>
                  <Link to="/register" className="btn btn-primary btn-sm">
                    Register
                  </Link>
                </>
              )}
            </div>
          </div>
        </nav>
      </div>
    </div>
  );
};

export default NavBar;

