import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import Search from './pages/search';
import Quotation from './pages/quotation';
import Dashboard from './pages/dashboard';

import BASE from './api';


function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [syncing, setSyncing] = useState(false);
  const [cart, setCart] = useState([]);
  const [theme, setTheme] = useState('light');
  const [externalSearch, setExternalSearch] = useState(null);
  const pageViewClass = `${currentPage}-view`;

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await axios.get(`${BASE}/refresh`);
      alert(`${res.data.message || 'Catalog sync started.'}\n\nPlease wait 30-60 seconds, then search.`);
    } catch (e) {
      alert('Sync failed. Please check backend status.');
    }
    setSyncing(false);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return (
          <Dashboard
            setCurrentPage={setCurrentPage}
            setExternalSearch={setExternalSearch}
            cart={cart}
            setCart={setCart}
          />
        );
      case 'search':
        return (
          <Search
            cart={cart}
            setCart={setCart}
            externalSearch={externalSearch}
            setExternalSearch={setExternalSearch}
          />
        );
      case 'quotation':
        return <Quotation cart={cart} setCart={setCart} />;
      default:
        return <Search cart={cart} setCart={setCart} />;
    }
  };

  return (
    <div className={`App ${theme === 'dark' ? 'dark-theme' : ''} ${pageViewClass}`}>
      <nav className="navbar">
        <div className="nav-shell">
          <div className="nav-brand">
            <img
              src="https://www.shreejiceramica.com/tiles/vadodara-logo.png"
              alt="Shreeji Ceramica"
              className="nav-company-logo"
            />
            <div className="nav-logo">
              <span className="nav-company-name">Shreeji Ceramica</span>
              <span className="nav-company-tagline">Redefining Luxury</span>
            </div>
          </div>

          <div className="nav-links">
            <button
              className={`nav-link-btn ${currentPage === 'dashboard' ? 'active' : ''}`}
              onClick={() => setCurrentPage('dashboard')}
            >
              Dashboard
            </button>
            <button
              className={`nav-link-btn ${currentPage === 'search' ? 'active' : ''}`}
              onClick={() => setCurrentPage('search')}
            >
              Search Products
            </button>
            <button
              className={`nav-link-btn ${currentPage === 'quotation' ? 'active' : ''}`}
              onClick={() => setCurrentPage('quotation')}
            >
              Create Quotation {cart.length > 0 && `(${cart.length})`}
            </button>
          </div>

          <div className="nav-actions">
            <button
              onClick={toggleTheme}
              className="theme-toggle"
              title="Toggle Light/Dark Mode"
              aria-pressed={theme === 'dark'}
            >
              {theme === 'light' ? 'Dark' : 'Light'}
            </button>

            <button className={`sync-btn ${syncing ? 'is-syncing' : ''}`} onClick={handleSync} disabled={syncing}>
              {syncing ? 'Syncing...' : 'Sync Catalogs'}
            </button>
          </div>
        </div>
      </nav>

      <main className="container">{renderPage()}</main>

      {cart.length > 0 && currentPage === 'search' && (
        <div
          style={{
            position: 'fixed',
            bottom: '2rem',
            right: '2rem',
            background: 'var(--primary-color)',
            color: '#fff',
            padding: '1rem 2rem',
            borderRadius: '2rem',
            fontWeight: 'bold',
            boxShadow: '0 10px 25px rgba(190,30,45,0.3)',
            cursor: 'pointer',
            zIndex: 100,
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            transition: 'transform 0.2s',
          }}
          onClick={() => setCurrentPage('quotation')}
          onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.05)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
        >
          <span>Cart: {cart.length} Item{cart.length > 1 ? 's' : ''} Added</span>
          <span
            style={{
              fontSize: '0.8rem',
              background: 'rgba(255,255,255,0.2)',
              padding: '0.2rem 0.5rem',
              borderRadius: '1rem',
            }}
          >
            View &rarr;
          </span>
        </div>
      )}

      <footer className="footer">&copy; {new Date().getFullYear()} Shreeji Ceramica &mdash; Redefining Luxury | Quotation Management System</footer>
    </div>
  );
}

export default App;
