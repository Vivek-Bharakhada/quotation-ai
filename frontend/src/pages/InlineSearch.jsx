import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './search.css';

import BASE from '../api';
import { resolveAssetUrl } from '../utils/url';

export default function InlineSearch({ onAdd }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const suggestionRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionRef.current && !suggestionRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (query.trim().length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    const timer = setTimeout(() => {
      setLoading(true);
      axios.get(`${BASE}/search-suggestions?q=${encodeURIComponent(query)}&brand=all`)
        .then(res => {
          const s = res.data.suggestions || [];
          setSuggestions(s);
          if (s.length > 0) setShowSuggestions(true);
          setLoading(false);
        })
        .catch(() => {
          setSuggestions([]);
          setLoading(false);
        });
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  const internalAdd = (s) => {
    if (!s) return;
    
    // Pick full data from raw_item (now provided by backend)
    const product = s.raw_item || {};
    const fullText = product.text || s.description || "";
    const nameOnly = fullText.split('\n')[0].trim() || s.description || "Product";
    
    // Price extraction logic
    let finalPrice = product.price || '';
    if (product.variant_prices && Object.keys(product.variant_prices).length > 0) {
      const v = Object.keys(product.variant_prices)[0];
      finalPrice = product.variant_prices[v];
    }
    if (!finalPrice || finalPrice === '0') {
      const match = fullText.match(/MRP[^\d]*([\d,]+)/i);
      if (match) finalPrice = match[1].replace(/,/g, '');
    }

    const newItem = {
      name: nameOnly,
      price: String(finalPrice || '0'),
      quantity: 1,
      discount: 0,
      image: (product.images && product.images[0]) || s.image || null,
      room: product.category || product.room || '',
      rawText: fullText,
      sku: product.sku || s.text || '',
      size: product.size || '',
    };

    console.log("ITEM READY TO ADD:", newItem);
    
    if (onAdd && typeof onAdd === 'function') {
      onAdd(newItem);
    } else {
      console.warn("onAdd PROP MISSING OR NOT A FUNCTION");
    }
    
    setQuery('');
    setSuggestions([]);
    setShowSuggestions(false);
  };

  return (
    <div style={{ position: 'relative', width: '100%' }} ref={suggestionRef}>
      <form style={{ display: 'flex', gap: '8px', alignItems: 'center' }} onSubmit={(e) => { e.preventDefault(); if (suggestions.length > 0) internalAdd(suggestions[0]); }}>
        <input
          className="sp-search-input"
          style={{ 
             flex: 1, 
             padding: '0.7rem 1rem', 
             borderRadius: '1rem', 
             border: '1px solid #ddd', 
             outline: 'none',
             fontSize: '0.9rem' 
          }}
          placeholder="Search Product e.g. 9272"
          value={query}
          autoComplete="off"
          onChange={(e) => {
            setQuery(e.target.value);
            setShowSuggestions(true);
          }}
        />
        <button 
           type="submit"
           style={{
              padding: '0.7rem 1.4rem', 
              borderRadius: '1rem', 
              background: '#be1e2d', 
              color: 'white', 
              border: 'none', 
              cursor: 'pointer',
              fontWeight: 'bold',
              fontSize: '0.85rem'
           }}
           disabled={loading}
        >
          {loading ? '...' : 'ADD'}
        </button>
      </form>

      {showSuggestions && suggestions.length > 0 && (
        <div 
          className="sp-suggestions-list"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            background: 'white',
            border: '1px solid #ddd',
            borderRadius: '1rem',
            marginTop: '8px',
            boxShadow: '0 10px 15px rgba(0,0,0,0.1)',
            zIndex: 99999,
            maxHeight: '400px',
            overflowY: 'auto',
            padding: '8px'
          }}
        >
          {suggestions.map((s, idx) => (
            <div 
              key={idx}
              className="sp-suggestion-item"
              onMouseDown={(e) => { e.preventDefault(); internalAdd(s); }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px',
                cursor: 'pointer',
                borderRadius: '8px',
                borderBottom: '1px solid #eee'
              }}
            >
              {s.image ? (
                <img src={resolveAssetUrl(s.image)} alt="" style={{ width: '50px', height: '50px', objectFit: 'contain' }} />
              ) : (
                <div style={{ width: '50px', height: '50px', background: '#f5f5f5', borderRadius: '4px', fontSize: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>NO IMG</div>
              )}
              <div style={{ flex: 1 }}>
                 <div style={{ fontWeight: 'bold', color: '#111' }}>{s.text}</div>
                 <div style={{ fontSize: '0.8rem', color: '#666' }}>{s.description}</div>
              </div>
              <div style={{ fontSize: '0.7rem', color: '#be1e2d', fontWeight: 'bold' }}>{(s.brand || 'Catalog').toUpperCase()}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
