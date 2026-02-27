import { useState } from 'react';
import axios from 'axios';
import './search.css';

import BASE from '../api';


export default function Search({ cart, setCart }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedBrand, setSelectedBrand] = useState('all');
  const [viewProduct, setViewProduct] = useState(null);
  const [failedImages, setFailedImages] = useState({});

  const isCodeOrModelQuery = (value) => {
    const q = (value || '').trim();
    if (!q) return false;
    const tokens = q.toLowerCase().match(/[a-z0-9/-]+/g) || [];
    if (!tokens.length) return false;
    if (tokens.some((tok) => /^[a-z]{1,5}[-/]?\d{2,}[a-z0-9/-]*$/i.test(tok))) return true;
    if (tokens.length === 1 && /^\d{3,}$/.test(tokens[0])) return true;
    if (tokens.length === 1 && /[a-z]/i.test(tokens[0]) && /\d/.test(tokens[0]) && tokens[0].length >= 4) return true;
    const hasNumericToken = tokens.some((tok) => /^\d{3,}$/.test(tok));
    const hasKnownBrand = tokens.some((tok) => tok === 'kohler' || tok === 'aquant');
    return tokens.length <= 3 && hasNumericToken && hasKnownBrand;
  };

  const handleSearch = async (brandOverride) => {
    const q = query.trim();
    if (!q) return;

    setLoading(true);
    setResults([]);

    const ts = Date.now();
    const brandParam = typeof brandOverride === 'string' ? brandOverride : selectedBrand;
    const brandQuery = brandParam !== 'all' ? `&brand=${brandParam}` : '';
    const exactQuery = isCodeOrModelQuery(q) ? '&exact=true' : '';

    axios
      .get(`${BASE}/search?q=${encodeURIComponent(q)}${brandQuery}${exactQuery}&smart=false&_t=${ts}`)
      .then((res) => {
        const apiResults = res.data.results || [];
        setResults(isCodeOrModelQuery(q) ? apiResults.slice(0, 1) : apiResults);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Search failed', err);
        setLoading(false);
      });
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

  return (
    <div className="sp-root">
      <header className="sp-head">
        <h2 className="sp-title">
          Accurate <span>Search</span>
        </h2>
        <p className="sp-subtitle">Find products by name, model number, or code instantly</p>
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

      <section className="sp-search-shell">
        <input
          className="sp-search-input"
          placeholder="e.g. 9272, K-28362IN, Shower Mixer..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />

        <button className="sp-search-btn" onClick={() => handleSearch()} disabled={loading}>
          {loading ? 'SEARCHING...' : 'SEARCH'}
        </button>
      </section>

      {loading && (
        <div className="sp-loading">
          <div className="spinner sp-spinner" />
          <div className="sp-loading-text">PRECISION SCANNING...</div>
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
                <h3 className="sp-card-title">{title}</h3>

                {r.price && r.price !== '0' && (
                  <div className="sp-price">MRP: Rs {parseInt(r.price, 10).toLocaleString()}</div>
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

      {!loading && results.length === 0 && query && (
        <div className="sp-empty">
          <h3>No exact match found</h3>
          <p>Try searching with just the model code. Example: 9272</p>
        </div>
      )}
    </div>
  );
}
