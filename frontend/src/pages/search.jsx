import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './search.css';

import BASE from '../api';


export default function Search({ cart, setCart, setFooterVisible }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedBrand, setSelectedBrand] = useState('all');
  const [viewProduct, setViewProduct] = useState(null);
  const [failedImages, setFailedImages] = useState({});
  const suggestionRef = useRef(null);

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

    const timer = setTimeout(() => {
      axios.get(`${BASE}/search-suggestions?q=${encodeURIComponent(query)}`)
        .then(res => {
          const list = res.data.suggestions || [];
          setSuggestions(list);
          if (list.length > 0) setShowSuggestions(true);
        })
        .catch(() => setSuggestions([]));
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  const handleSearch = async (overrideQuery, brandOverride) => {
    const q = (typeof overrideQuery === 'string' ? overrideQuery : query).trim();
    if (!q) return;

    setLoading(true);
    setResults([]);
    setShowSuggestions(false);

    const ts = Date.now();
    const brandParam = typeof brandOverride === 'string' ? brandOverride : selectedBrand;
    const brandQuery = brandParam !== 'all' ? `&brand=${brandParam}` : '';
    const exactQuery = '&exact=true';

    axios
      .get(`${BASE}/search?q=${encodeURIComponent(q)}${brandQuery}${exactQuery}&smart=false&_t=${ts}`)
      .then((res) => {
        const apiResults = res.data.results || [];
        setResults(apiResults);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Search failed', err);
        setLoading(false);
      });
  };

  const selectSuggestion = (s) => {
    setQuery(s.text);
    setShowSuggestions(false);
    handleSearch(s.text);
  };

  const addToCart = (product) => {
    const lines = product.text.split('\n');
    const name = lines[0]?.trim() || 'Unknown Product';

    let price = product.price || '';
    if (!price || price === '0') {
      const mrpMatch = product.text.match(/MRP[^\d]*([\d,]+)/i);
      if (mrpMatch) {
        price = mrpMatch[1].replace(/,/g, '');
      } else {
        const allNumbers = product.text.match(/[\d,]{4,}/g);
        if (allNumbers && allNumbers.length > 0) {
          price = allNumbers[allNumbers.length - 1].replace(/,/g, '');
        }
      }
    }

    const newItem = {
      id: product.text,
      name,
      price,
      rawText: product.text,
      image: product.images && product.images.length > 0 ? product.images[0] : null,
    };

    setCart((prev) => [...prev, newItem]);
  };

  const isInCart = (productText) => cart?.some((item) => item.id === productText);
  const markImageFailed = (src) => {
    if (!src) return;
    setFailedImages((prev) => (prev[src] ? prev : { ...prev, [src]: true }));
  };

  const foundBrands = new Set(results.map((item) => (item.brand || '').toLowerCase()).filter(Boolean));
  const missingBrands = ['Aquant', 'Kohler'].filter((brand) => !foundBrands.has(brand.toLowerCase()));
  const showSearchSummary = !loading && query && results.length > 0;

  let searchSummary = '';
  if (showSearchSummary) {
    if (selectedBrand === 'all') {
      if (results.length >= 2) {
        searchSummary = 'Best exact match from both PDFs.';
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
          <img src="/hero.png" alt="Luxury Bathroom" className="sp-hero-img" />
        </div>
      </header>

      <section className="sp-brand-wrap">
        <div className="sp-brand-tabs">
          {['all', 'Aquant', 'Kohler'].map((brand) => (
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
            onChange={(e) => setQuery(e.target.value)}
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
                    <img src={`${BASE}${s.image}`} alt="" className="sp-sugg-img" />
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
          const added = isInCart(r.text);
          const title = r.text.split('\n')[0].substring(0, 100);
          const imageCandidates = (r.images || []).filter(Boolean).map((p) => `${BASE}${p}`);
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
                  <img src={imageSrc} alt="Product" onError={() => markImageFailed(imageSrc)} />
                ) : (
                  <div className="sp-no-preview">IMAGE NOT FOUND</div>
                )}
              </div>

              <div className="sp-card-body">
                <div className="sp-meta-row">
                  <span className="sp-meta-pill">{(r.brand || 'Catalog').toUpperCase()}</span>
                </div>

                <h3 className="sp-card-title">{title}</h3>

                {r.price && r.price !== '0' && (
                  <div className="sp-price">MRP: {parseInt(r.price, 10).toLocaleString('en-IN')}</div>
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

