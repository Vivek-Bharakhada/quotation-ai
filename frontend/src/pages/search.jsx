import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './search.css';

import BASE from '../api';
import { readJson, writeJson } from '../utils/storage';
import { resolveAssetUrl } from '../utils/url';

const SEARCH_UI_KEY = 'quotation-ai/search-ui';
const SEARCH_CACHE_KEY = 'quotation-ai/search-cache';
const SEARCH_CACHE_LIMIT = 12;

const buildSearchKey = (query, brand) =>
  `${String(brand || 'all').toLowerCase()}::${String(query || '').trim().toLowerCase()}`;

const getStoredSearchUi = () => {
  const stored = readJson(SEARCH_UI_KEY, {});
  return stored && typeof stored === 'object' ? stored : {};
};

const getStoredSearchCache = () => {
  const stored = readJson(SEARCH_CACHE_KEY, {});
  return stored && typeof stored === 'object' ? stored : {};
};

const saveCachedSearch = (query, brand, results) => {
  if (!query || !Array.isArray(results)) {
    return;
  }

  const key = buildSearchKey(query, brand);
  const current = getStoredSearchCache();
  const nextEntries = {
    ...current,
    [key]: {
      query,
      brand,
      results: results.slice(0, 12),
      updatedAt: Date.now(),
    },
  };

  const trimmed = Object.entries(nextEntries)
    .sort(([, left], [, right]) => (right.updatedAt || 0) - (left.updatedAt || 0))
    .slice(0, SEARCH_CACHE_LIMIT)
    .reduce((accumulator, [entryKey, value]) => {
      accumulator[entryKey] = value;
      return accumulator;
    }, {});

  writeJson(SEARCH_CACHE_KEY, trimmed);
};

export default function Search({ cart, setCart, setFooterVisible }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedBrand, setSelectedBrand] = useState('all');
  const [viewProduct, setViewProduct] = useState(null);
  const [failedImages, setFailedImages] = useState({});
  const [selectedVariants, setSelectedVariants] = useState({});
  const [searchMode, setSearchMode] = useState('idle');
  const [isOffline, setIsOffline] = useState(() => (typeof navigator === 'undefined' ? false : !navigator.onLine));
  const suggestionRef = useRef(null);
  const lastBrandRef = useRef(selectedBrand);

  // Sync footer visibility with suggestions
  useEffect(() => {
    if (setFooterVisible) {
      setFooterVisible(!showSuggestions);
    }
    // Cleanup to ensure footer comes back when leaving search page
    return () => setFooterVisible && setFooterVisible(true);
  }, [showSuggestions, setFooterVisible]);

  // Handle clicking outside suggestions
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionRef.current && !suggestionRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch suggestions when query changes
  useEffect(() => {
    if (query.trim().length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    if (isOffline) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const timer = setTimeout(() => {
      axios.get(`${BASE}/search-suggestions?q=${encodeURIComponent(query)}&brand=${selectedBrand}`)
        .then(res => {
          const list = res.data.suggestions || [];
          setSuggestions(list);
        })
        .catch(() => setSuggestions([]));
    }, 250);

    return () => clearTimeout(timer);
  }, [query, selectedBrand, isOffline]);

  // Re-trigger search when brand changes
  useEffect(() => {
    const brandChanged = lastBrandRef.current !== selectedBrand;
    lastBrandRef.current = selectedBrand;

    if (brandChanged && query.trim()) {
      handleSearch(query, selectedBrand);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBrand, query]);

  useEffect(() => {
    writeJson(SEARCH_UI_KEY, {
      selectedBrand,
      selectedVariants,
      searchMode,
    });
  }, [selectedBrand, selectedVariants, searchMode]);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleSearch = async (overrideQuery, brandOverride) => {
    const q = (typeof overrideQuery === 'string' ? overrideQuery : query).trim();
    if (!q) return;

    const brandParam = typeof brandOverride === 'string' ? brandOverride : selectedBrand;
    const cache = getStoredSearchCache();
    const cachedEntry = cache[buildSearchKey(q, brandParam)];

    if (isOffline) {
      setLoading(false);
      setShowSuggestions(false);
      setResults(cachedEntry?.results || []);
      setSearchMode(cachedEntry?.results?.length ? 'offline-cache' : 'offline-miss');
      return;
    }

    setLoading(true);
    setResults([]);
    setShowSuggestions(false);
    setSearchMode('loading');

    const ts = Date.now();
    const brandQuery = brandParam !== 'all' ? `&brand=${brandParam}` : '';
    const exactQuery = '&exact=true';

    axios
      .get(`${BASE}/search?q=${encodeURIComponent(q)}${brandQuery}${exactQuery}&smart=false&_t=${ts}`)
      .then((res) => {
        const apiResults = res.data.results || [];
        setResults(apiResults);
        setSearchMode('online');
        saveCachedSearch(q, brandParam, apiResults);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Search failed', err);
        const fallbackResults = cachedEntry?.results || [];
        setResults(fallbackResults);
        setSearchMode(fallbackResults.length ? 'offline-cache' : 'error');
        setLoading(false);
      });
  };

  const selectSuggestion = (s) => {
    setQuery(s.text);
    setShowSuggestions(false);
    handleSearch(s.text, selectedBrand);
  };

  const addToCart = (product, forcedVariant = null) => {
    const lines = product.text.split('\n');
    const baseName = lines[0]?.trim() || 'Unknown Product';

    let finalPrice = product.price || '';
    let finalVariant = forcedVariant || selectedVariants[product.text] || (product.variant_prices && Object.keys(product.variant_prices)[0]) || '';
    
    if (product.variant_prices && finalVariant && product.variant_prices[finalVariant]) {
      finalPrice = product.variant_prices[finalVariant];
    }

    if (!finalPrice || finalPrice === '0') {
      const mrpMatch = product.text.match(/MRP[^\d]*([\d,]+)/i);
      if (mrpMatch) {
        finalPrice = mrpMatch[1].replace(/,/g, '');
      } else {
        const allNumbers = product.text.match(/[\d,]{4,}/g);
        if (allNumbers && allNumbers.length > 0) {
          finalPrice = allNumbers[allNumbers.length - 1].replace(/,/g, '');
        }
      }
    }

    const displayName = finalVariant ? `${baseName} (${finalVariant})` : baseName;

    const newItem = {
      id: `${product.text}-${finalVariant}`,
      name: displayName,
      price: finalPrice,
      rawText: product.text,
      image: product.images && product.images.length > 0 ? product.images[0] : null,
      brand: product.brand,
      finish: finalVariant
    };

    setCart((prev) => [...prev, newItem]);
  };

  const isInCart = (productText) => cart?.some((item) => item.id === productText);
  const markImageFailed = (src) => {
    if (!src) return;
    setFailedImages((prev) => (prev[src] ? prev : { ...prev, [src]: true }));
  };

  const foundBrands = new Set(results.map((item) => (item.brand || '').toLowerCase()).filter(Boolean));
  const missingBrands = ['Aquant', 'Kohler', 'Plumber'].filter((brand) => !foundBrands.has(brand.toLowerCase()));
  const showSearchSummary = !loading && query && results.length > 0;

  let statusMessage = '';
  if (isOffline && searchMode === 'offline-cache') {
    statusMessage = 'Offline mode: showing cached search results from your previous online search.';
  } else if (isOffline && searchMode === 'offline-miss') {
    statusMessage = 'Offline mode: this query is not cached yet. Go online once to fetch and save it.';
  } else if (!isOffline && searchMode === 'error') {
    statusMessage = 'Live search failed. Please check your backend URL or internet connection.';
  } else if (isOffline && !query) {
    statusMessage = 'Offline mode is active. Quotation drafts and saved cart still work.';
  }

  let searchSummary = '';
  if (showSearchSummary) {
    if (selectedBrand === 'all') {
      if (results.length >= 2) {
        searchSummary = 'Best exact match from various catalogs.';
      } else {
        const matchedBrand = results[0]?.brand || 'selected catalog';
        const missingLabel = missingBrands.join(' + ');
        searchSummary = missingLabel
          ? `Exact match mila: ${matchedBrand}. ${missingLabel} me is query ka match nahi mila.`
          : `Exact match mila: ${matchedBrand}.`;
      }
    } else {
      searchSummary = `Showing best exact ${selectedBrand} match.`;
    }
  }

  return (
    <div className="sp-root">
      <header className="sp-hero">
        <div className="sp-hero-content">
          <h1 className="sp-hero-title">
            Discover <span>Luxury</span>
          </h1>
          <p className="sp-hero-subtitle">Search through thousands of premium bathroom fittings and tiles</p>
        </div>
        <div className="sp-hero-visual">
          <img src="/hero.png" alt="Luxury Bathroom" loading="lazy" className="sp-hero-img" />
        </div>
      </header>

      <section className="sp-brand-wrap">
        <div className="sp-brand-tabs">
          {['all', 'Aquant', 'Kohler', 'Plumber'].map((brand) => (
            <button
              key={brand}
              onClick={() => setSelectedBrand(brand)}
              className={`sp-brand-btn ${selectedBrand === brand ? 'active' : ''}`}
            >
              {brand.toUpperCase()}
            </button>
          ))}
        </div>
      </section>

      <div className="sp-search-container" ref={suggestionRef}>
        <section className="sp-search-shell">
          <input
            className="sp-search-input"
            placeholder="e.g. 9272, K-28362IN, Shower Mixer..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          />

          <button className="sp-search-btn" onClick={() => handleSearch()} disabled={loading}>
            {loading ? 'SEARCHING...' : 'SEARCH'}
          </button>
        </section>

        {showSuggestions && (
          <div className="sp-suggestions-list">
            {suggestions.map((s, idx) => (
              <div
                key={idx}
                className="sp-suggestion-item"
                onClick={() => selectSuggestion(s)}
              >
                <div className="sp-sugg-left">
                  {s.image ? (
                    <img src={resolveAssetUrl(s.image)} alt="" loading="lazy" className="sp-sugg-img" />
                  ) : (
                    <div className="sp-sugg-no-img">NO IMG</div>
                  )}
                  <div className="sp-sugg-info">
                    <span className="sp-sugg-text">{s.text}</span>
                    <span className="sp-sugg-desc">{s.description}</span>
                  </div>
                </div>
                <span className="sp-sugg-brand">{(s.brand || 'Aquant').toUpperCase()}</span>
              </div>
            ))}
          </div>
        )}

      </div>

      {statusMessage && <div className={`sp-status-banner ${isOffline ? 'offline' : 'error'}`}>{statusMessage}</div>}

      {showSearchSummary && <div className="sp-search-summary">{searchSummary}</div>}

      {loading && (
        <div className="sp-loading-shimmer">
          {[1, 2, 3, 4, 5, 6].map(n => (
            <div key={n} className="sp-shimmer-card">
              <div className="sp-shimmer-media"></div>
              <div className="sp-shimmer-line"></div>
              <div className="sp-shimmer-line short"></div>
            </div>
          ))}
        </div>
      )}

      <section className="sp-grid">
        {results.map((r, i) => {
          const currentVariant = selectedVariants[r.text] || (r.variant_prices && Object.keys(r.variant_prices)[0]) || '';
          const displayPrice = (r.variant_prices && currentVariant && r.variant_prices[currentVariant]) || r.price;
          
          const added = isInCart(`${r.text}-${currentVariant}`);
          const title = r.text.split('\n')[0].substring(0, 100);
          const imageCandidates = (r.images || []).filter(Boolean).map(resolveAssetUrl);
          const imageSrc = imageCandidates.find((src) => !failedImages[src]) || '';
          const hasImage = imageSrc && !failedImages[imageSrc];

          return (
            <article
              key={i}
              className={`sp-card ${added ? 'added' : ''}`}
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <div className="sp-media">
                {hasImage ? (
                  <img src={imageSrc} alt="Product" loading="lazy" onError={() => markImageFailed(imageSrc)} />
                ) : (
                  <div className="sp-no-preview">IMAGE NOT FOUND</div>
                )}
              </div>

              <div className="sp-card-body">
                <div className="sp-meta-row">
                  <span className="sp-meta-pill">{(r.brand || 'Catalog').toUpperCase()}</span>
                </div>

                <h3 className="sp-card-title">{title}</h3>

                {r.variant_prices && Object.keys(r.variant_prices).length > 0 && (
                  <div className="sp-variant-selector">
                    <span className="sp-variant-label">Select Finish / Variant</span>
                    <select 
                      className="sp-variant-select"
                      value={selectedVariants[r.text] || Object.keys(r.variant_prices)[0]}
                      onChange={(e) => setSelectedVariants(prev => ({...prev, [r.text]: e.target.value}))}
                    >
                      {Object.keys(r.variant_prices).map(v => (
                        <option key={v} value={v}>{v} - ₹{parseInt(r.variant_prices[v], 10).toLocaleString('en-IN')}</option>
                      ))}
                    </select>
                  </div>
                )}

                {displayPrice && displayPrice !== '0' && (
                  <div className="sp-price">
                    {(r.brand || '').toLowerCase() === 'plumber' ? 'MRP Per Unit: ' : 'MRP: '}
                    ₹{parseInt(displayPrice, 10).toLocaleString('en-IN')}
                    {currentVariant && <span className="sp-price-variant-tag"> ({currentVariant})</span>}
                  </div>
                )}

                <div className="sp-actions">
                  <button
                    className={`sp-add-btn ${added ? 'added' : ''}`}
                    onClick={() => !added && addToCart(r)}
                    disabled={added}
                  >
                    {added ? 'ADDED TO BILL' : 'ADD TO QUOTATION'}
                  </button>

                  <button className="sp-info-btn" onClick={() => setViewProduct(r)}>
                    INFO
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </section>

      {viewProduct && (
        <div className="sp-modal-overlay" onClick={() => setViewProduct(null)}>
          <div className="sp-modal-card" onClick={(e) => e.stopPropagation()}>
            <h2>Product Details</h2>
            <div className="sp-details">{viewProduct.text}</div>
            <button
              className="sp-select-btn"
              onClick={() => {
                addToCart(viewProduct);
                setViewProduct(null);
              }}
            >
              SELECT THIS PRODUCT
            </button>
          </div>
        </div>
      )}

      {!loading && results.length === 0 && query && !showSuggestions && (
        <div className="sp-empty">
          <h3>No exact match found</h3>
          <p>Try searching with just the model code. Example: 9272</p>
        </div>
      )}
    </div>
  );
}
