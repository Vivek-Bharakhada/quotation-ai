import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './App.css';
import Search from './pages/search';
import Quotation from './pages/quotation';
import Dashboard from './pages/dashboard';

import BASE, {
  clearApiBaseOverride,
  getApiBase,
  hasApiBaseOverride,
  setApiBaseOverride,
} from './api';
import { readJson, readString, writeJson, writeString } from './utils/storage';

const APP_STATE_KEYS = {
  cart: 'quotation-ai/cart',
  page: 'quotation-ai/current-page',
  theme: 'quotation-ai/theme',
};

const ALLOWED_PAGES = new Set(['dashboard', 'search', 'quotation']);

function getStandaloneMode() {
  if (typeof window === 'undefined') {
    return false;
  }

  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true
  );
}

function getInitialPage() {
  return 'dashboard';
}

function getInitialCart() {
  const storedCart = readJson(APP_STATE_KEYS.cart, []);
  return Array.isArray(storedCart) ? storedCart : [];
}

function getInitialTheme() {
  return readString(APP_STATE_KEYS.theme, 'light') === 'dark' ? 'dark' : 'light';
}

function App() {
  const [currentPage, setCurrentPage] = useState(getInitialPage);
  const [syncing, setSyncing] = useState(false);
  const [cart, setCart] = useState(getInitialCart);
  const [theme, setTheme] = useState(getInitialTheme);
  const [externalSearch, setExternalSearch] = useState(null);
  const [footerVisible, setFooterVisible] = useState(true);
  const [isOnline, setIsOnline] = useState(() => (typeof navigator === 'undefined' ? true : navigator.onLine));
  const [installPrompt, setInstallPrompt] = useState(null);
  const [installHelp, setInstallHelp] = useState('');
  const [isInstalled, setIsInstalled] = useState(getStandaloneMode);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [apiBaseInput, setApiBaseInput] = useState(() => getApiBase());
  const [apiOverrideActive, setApiOverrideActive] = useState(() => hasApiBaseOverride());
  const [menuOpen, setMenuOpen] = useState(false);
  const pageViewClass = `${currentPage}-view`;

  useEffect(() => {
    writeString(APP_STATE_KEYS.page, currentPage);
    setMenuOpen(false);
  }, [currentPage]);

  useEffect(() => {
    writeJson(APP_STATE_KEYS.cart, cart);
  }, [cart]);

  useEffect(() => {
    writeString(APP_STATE_KEYS.theme, theme);
  }, [theme]);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    const mediaQuery =
      typeof window !== 'undefined' && window.matchMedia
        ? window.matchMedia('(display-mode: standalone)')
        : null;

    const syncStandaloneState = () => setIsInstalled(getStandaloneMode());
    const handleBeforeInstallPrompt = (event) => {
      event.preventDefault();
      setInstallPrompt(event);
      setInstallHelp('');
    };
    const handleAppInstalled = () => {
      setIsInstalled(true);
      setInstallPrompt(null);
      setInstallHelp('App installed successfully.');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    if (mediaQuery) {
      if (typeof mediaQuery.addEventListener === 'function') {
        mediaQuery.addEventListener('change', syncStandaloneState);
      } else if (typeof mediaQuery.addListener === 'function') {
        mediaQuery.addListener(syncStandaloneState);
      }
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);

      if (mediaQuery) {
        if (typeof mediaQuery.removeEventListener === 'function') {
          mediaQuery.removeEventListener('change', syncStandaloneState);
        } else if (typeof mediaQuery.removeListener === 'function') {
          mediaQuery.removeListener(syncStandaloneState);
        }
      }
    };
  }, []);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await axios.get(`${BASE}/refresh`);
      alert(`${res.data.message || 'Catalog sync started.'}\n\nPlease wait 30-60 seconds, then search.`);
    } catch (error) {
      console.error(error);
      alert('Sync failed. Please check backend status.');
    }
    setSyncing(false);
  };

  const handleInstallApp = async () => {
    if (installPrompt) {
      installPrompt.prompt();
      const choice = await installPrompt.userChoice;
      if (choice?.outcome === 'accepted') {
        setInstallHelp('Installing app...');
      } else {
        setInstallHelp('Install skipped. You can install later from the browser menu.');
      }
      setInstallPrompt(null);
      return;
    }

    setInstallHelp('Use your browser menu and choose "Install app" or "Add to Home Screen".');
  };

  const openSettings = () => {
    setApiBaseInput(getApiBase());
    setApiOverrideActive(hasApiBaseOverride());
    setSettingsOpen(true);
  };

  const saveApiSettings = () => {
    const normalized = String(apiBaseInput || '').trim();
    if (!/^https?:\/\//i.test(normalized)) {
      alert('Please enter a valid backend URL starting with http:// or https://');
      return;
    }

    setApiBaseOverride(normalized);
    setApiOverrideActive(true);
    setSettingsOpen(false);
    window.location.reload();
  };

  const resetApiSettings = () => {
    clearApiBaseOverride();
    setApiOverrideActive(false);
    setSettingsOpen(false);
    window.location.reload();
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
            setFooterVisible={setFooterVisible}
          />
        );
      case 'quotation':
        return <Quotation cart={cart} />;
      default:
        return <Search cart={cart} setCart={setCart} setFooterVisible={setFooterVisible} />;
    }
  };

  return (
    <div className={`App ${theme === 'dark' ? 'dark-theme' : ''} ${pageViewClass}`}>
      <div className="App-grain" />
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

          <button
            className="hamburger-menu"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle navigation menu"
            aria-expanded={menuOpen}
          >
            <span></span>
            <span></span>
            <span></span>
          </button>

          <div className={`nav-links ${menuOpen ? 'mobile-open' : ''}`}>
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
            <div className="nav-meta">
              <span className={`status-chip ${isOnline ? 'online' : 'offline'}`}>
                {isOnline ? 'Online' : 'Offline'}
              </span>
              <span className={`status-chip ${isInstalled ? 'installed' : 'browser'}`}>
                {isInstalled ? 'App Mode' : 'Browser Mode'}
              </span>
            </div>

            {!isInstalled && (
              <button onClick={handleInstallApp} className="install-btn" title="Install this app">
                Install App
              </button>
            )}

            <button
              onClick={toggleTheme}
              className="theme-toggle"
              title="Toggle Light/Dark Mode"
              aria-pressed={theme === 'dark'}
            >
              {theme === 'light' ? 'Dark' : 'Light'}
            </button>

            <button className="nav-icon-btn" onClick={openSettings} title="App and backend settings">
              Settings
            </button>

            <button className={`sync-btn ${syncing ? 'is-syncing' : ''}`} onClick={handleSync} disabled={syncing}>
              {syncing ? 'Syncing...' : 'Sync Catalogs'}
            </button>
          </div>
        </div>
      </nav>

      <main className="container">
        {(installHelp || !isOnline || apiOverrideActive) && (
          <div className={`app-banner ${isOnline ? 'info' : 'warning'}`}>
            {!isOnline && <span>You are offline. Cached drafts and previous results will still be available.</span>}
            {isOnline && installHelp && <span>{installHelp}</span>}
            {apiOverrideActive && (
              <span>
                Custom backend active: <strong>{getApiBase()}</strong>
              </span>
            )}
          </div>
        )}

        {renderPage()}
        {footerVisible && (
          <footer className="footer">
            &copy; {new Date().getFullYear()} Shreeji Ceramica | Quotation Management System
          </footer>
        )}
      </main>

      {cart.length > 0 && currentPage === 'search' && (
        <div
          className="floating-cart"
          onClick={() => setCurrentPage('quotation')}
          onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.05)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
        >
          <span>Cart: {cart.length} Item{cart.length > 1 ? 's' : ''} Added</span>
          <span className="floating-cart-pill">View &rarr;</span>
        </div>
      )}

      {settingsOpen && (
        <div className="app-modal-overlay" onClick={() => setSettingsOpen(false)}>
          <div className="app-settings-card" onClick={(event) => event.stopPropagation()}>
            <div className="app-settings-head">
              <div>
                <h2>App Settings</h2>
                <p>Use a deployed FastAPI backend so the app works on phone, iPhone, tablet, and desktop.</p>
              </div>
              <button className="app-settings-close" onClick={() => setSettingsOpen(false)}>
                x
              </button>
            </div>

            <label className="app-settings-label" htmlFor="api-base-input">
              Backend API URL
            </label>
            <input
              id="api-base-input"
              className="app-settings-input"
              value={apiBaseInput}
              onChange={(event) => setApiBaseInput(event.target.value)}
              placeholder="https://your-backend-domain.com"
            />

            <div className="app-settings-note">
              Current frontend target: <strong>{BASE}</strong>
            </div>

            <div className="app-settings-actions">
              <button className="app-settings-btn primary" onClick={saveApiSettings}>
                Save And Reload
              </button>
              <button className="app-settings-btn" onClick={resetApiSettings}>
                Reset Default
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
