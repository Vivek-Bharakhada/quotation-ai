import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import './search.css';

import BASE from '../api';
import { resolveAssetUrl } from '../utils/url';

const MIN_QUERY_LENGTH = 2;
const MAX_MENU_HEIGHT = 380;
const VIEWPORT_PADDING = 12;

export default function InlineSearch({ onAdd, disabled = false }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [menuStyle, setMenuStyle] = useState(null);
  const [menuPlacement, setMenuPlacement] = useState('down');
  const [error, setError] = useState('');
  const suggestionRef = useRef(null);
  const inputRef = useRef(null);
  const menuRef = useRef(null);

  const resetSuggestions = () => {
    setSuggestions([]);
    setShowSuggestions(false);
    setLoading(false);
    setError('');
    setMenuStyle(null);
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      const clickedInsideField = suggestionRef.current && suggestionRef.current.contains(event.target);
      const clickedInsideMenu = menuRef.current && menuRef.current.contains(event.target);

      if (!clickedInsideField && !clickedInsideMenu) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (disabled) {
      setQuery('');
      resetSuggestions();
      return;
    }

    const trimmedQuery = query.trim();
    if (trimmedQuery.length < MIN_QUERY_LENGTH) {
      resetSuggestions();
      return;
    }

    const controller = new AbortController();
    const timer = setTimeout(() => {
      setLoading(true);
      setError('');
      setSuggestions([]);

      axios.get(`${BASE}/search-suggestions`, {
        params: { q: trimmedQuery, brand: 'all', limit: 50 },
        signal: controller.signal,
      })
        .then((res) => {
          if (controller.signal.aborted) {
            return;
          }

          const nextSuggestions = Array.isArray(res.data?.suggestions) ? res.data.suggestions : [];
          setSuggestions(nextSuggestions);
          setShowSuggestions(true);
        })
        .catch((err) => {
          if (controller.signal.aborted) {
            return;
          }

          console.error('Failed to load suggestions', err);
          setSuggestions([]);
          setError('Search suggestions unavailable. Please try again.');
          setShowSuggestions(true);
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setLoading(false);
          }
        });
    }, 250);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, disabled]);

  useEffect(() => {
    if (!showSuggestions || disabled || !inputRef.current) {
      setMenuStyle(null);
      return;
    }

    const updateMenuPosition = () => {
      if (!inputRef.current) {
        return;
      }

      const inputRect = inputRef.current.getBoundingClientRect();
      const estimatedMenuHeight = Math.min(menuRef.current?.scrollHeight || 280, MAX_MENU_HEIGHT);
      const spaceBelow = window.innerHeight - inputRect.bottom;
      const spaceAbove = inputRect.top;
      const nextPlacement = spaceBelow < estimatedMenuHeight + 24 && spaceAbove > spaceBelow ? 'up' : 'down';
      const nextWidth = Math.min(
        Math.max(inputRect.width, 260),
        window.innerWidth - VIEWPORT_PADDING * 2
      );
      const nextLeft = Math.min(
        Math.max(inputRect.left, VIEWPORT_PADDING),
        window.innerWidth - VIEWPORT_PADDING - nextWidth
      );
      const nextTop = nextPlacement === 'up'
        ? Math.max(VIEWPORT_PADDING, inputRect.top - estimatedMenuHeight - 10)
        : Math.min(
            window.innerHeight - VIEWPORT_PADDING - estimatedMenuHeight,
            inputRect.bottom + 10
          );

      setMenuPlacement(nextPlacement);
      setMenuStyle({
        position: 'fixed',
        top: `${nextTop}px`,
        left: `${nextLeft}px`,
        width: `${nextWidth}px`,
      });
    };

    updateMenuPosition();
    window.addEventListener('resize', updateMenuPosition);
    window.addEventListener('scroll', updateMenuPosition, true);

    return () => {
      window.removeEventListener('resize', updateMenuPosition);
      window.removeEventListener('scroll', updateMenuPosition, true);
    };
  }, [showSuggestions, disabled, loading, suggestions.length, error]);

  const internalAdd = (s) => {
    if (!s || disabled) return;

    // Pick full data from raw_item (now provided by backend)
    const product = s.raw_item || {};
    const fullText = product.text || s.description || '';
    const nameOnly = fullText.split('\n')[0].trim() || s.description || 'Product';

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
      room: '',
      rawText: fullText,
      sku: product.sku || s.text || '',
      size: product.size || '',
    };

    console.log('ITEM READY TO ADD:', newItem);

    if (onAdd && typeof onAdd === 'function') {
      onAdd(newItem);
    } else {
      console.warn('onAdd PROP MISSING OR NOT A FUNCTION');
    }

    setQuery('');
    resetSuggestions();
  };

  const trimmedQuery = query.trim();
  const hasResults = suggestions.length > 0;
  const showMenu = !disabled && showSuggestions && trimmedQuery.length >= MIN_QUERY_LENGTH;

  const menuContent = showMenu ? (
    <div
      ref={menuRef}
      className="sp-suggestions-list"
      style={{
        ...menuStyle,
        maxHeight: `${MAX_MENU_HEIGHT}px`,
        overflowY: 'auto',
        padding: '0.75rem',
        position: 'fixed',
        zIndex: 15000,
        borderRadius: '1.25rem',
        border: '1px solid rgba(95, 99, 104, 0.22)',
        borderTop: menuPlacement === 'up' ? '1px solid rgba(95, 99, 104, 0.22)' : '4px solid var(--primary-color)',
        borderBottom: menuPlacement === 'up' ? '4px solid var(--primary-color)' : '1px solid rgba(95, 99, 104, 0.22)',
        background: 'var(--surface-color)',
        color: 'var(--text-primary)',
        boxShadow: '0 30px 60px -28px rgba(0, 0, 0, 0.65)',
        backdropFilter: 'blur(18px)',
        WebkitBackdropFilter: 'blur(18px)',
      }}
    >
      {loading && (
        <div
          style={{
            padding: '0.85rem 0.95rem',
            borderRadius: '0.9rem',
            border: '1px solid rgba(95, 99, 104, 0.16)',
            background: 'var(--bg-color)',
            color: 'var(--text-secondary)',
            fontSize: '0.9rem',
            fontWeight: 700,
          }}
        >
          Searching suggestions...
        </div>
      )}

      {!loading && error && (
        <div
          style={{
            padding: '0.85rem 0.95rem',
            borderRadius: '0.9rem',
            border: '1px solid rgba(248, 113, 113, 0.22)',
            background: 'rgba(248, 113, 113, 0.08)',
            color: '#fecaca',
            fontSize: '0.9rem',
            fontWeight: 700,
          }}
        >
          {error}
        </div>
      )}

      {!loading && !error && !hasResults && (
        <div
          style={{
            padding: '0.85rem 0.95rem',
            borderRadius: '0.9rem',
            border: '1px dashed rgba(95, 99, 104, 0.3)',
            background: 'var(--bg-color)',
            color: 'var(--text-secondary)',
            fontSize: '0.9rem',
            fontWeight: 600,
          }}
        >
          No suggestions found for "{trimmedQuery}".
        </div>
      )}

      {!loading && !error && hasResults && suggestions.map((s, idx) => (
        <div
          key={
            s?.raw_item?.search_code
            || s?.raw_item?.name
            || s?.full_name
            || s?.text
            || idx
          }
          className="sp-suggestion-item"
          onMouseDown={(e) => {
            e.preventDefault();
            internalAdd(s);
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '10px 12px',
            cursor: 'pointer',
            borderRadius: '12px',
            border: '1px solid rgba(95, 99, 104, 0.12)',
            background: 'var(--bg-color)',
            marginBottom: idx === suggestions.length - 1 ? 0 : '8px',
            transition: 'transform 0.2s ease, background-color 0.2s ease, border-color 0.2s ease',
          }}
        >
          {s.image ? (
            <img
              src={resolveAssetUrl(s.image)}
              alt=""
              style={{
                width: '52px',
                height: '52px',
                objectFit: 'contain',
                background: '#ffffff',
                borderRadius: '10px',
                padding: '4px',
                flexShrink: 0,
              }}
            />
          ) : (
            <div
              style={{
                width: '52px',
                height: '52px',
                background: 'var(--bg-color)',
                borderRadius: '10px',
                fontSize: '10px',
                color: 'var(--text-secondary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                border: '1px dashed rgba(95, 99, 104, 0.3)',
              }}
            >
              NO IMG
            </div>
          )}

          <div style={{ flex: 1, minWidth: 0 }}>
            <div
              style={{
                fontWeight: 800,
                color: 'var(--text-primary)',
                lineHeight: 1.35,
                whiteSpace: 'normal',
                overflowWrap: 'anywhere',
              }}
            >
              {s.full_name || [s.text, s.description].filter(Boolean).join(' - ')}
            </div>
            <div
              style={{
                fontSize: '0.82rem',
                color: 'var(--text-secondary)',
                marginTop: '0.2rem',
                lineHeight: 1.4,
                whiteSpace: 'normal',
                overflowWrap: 'anywhere',
              }}
            >
              {s.full_name && s.text && s.full_name !== s.text ? `Code: ${s.text}` : s.description}
            </div>
          </div>

          <div
            style={{
              fontSize: '0.68rem',
              color: 'var(--primary-color)',
              fontWeight: 800,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              background: 'var(--primary-gradient)',
              borderRadius: '999px',
              padding: '0.45rem 0.75rem',
              flexShrink: 0,
            }}
          >
            {(s.brand || 'Catalog').toUpperCase()}
          </div>
        </div>
      ))}
    </div>
  ) : null;

  return (
    <div style={{ position: 'relative', width: '100%' }} ref={suggestionRef}>
      <form
        style={{ display: 'flex', gap: '8px', alignItems: 'center' }}
        onSubmit={(e) => {
          e.preventDefault();
          if (suggestions.length > 0) {
            internalAdd(suggestions[0]);
          }
        }}
      >
        <input
          ref={inputRef}
          className="sp-search-input"
          style={{
            flex: 1,
            padding: '0.7rem 1rem',
            borderRadius: '1rem',
            border: '1px solid #ddd',
            outline: 'none',
            fontSize: '0.9rem',
          }}
          placeholder="Search Product e.g. 4000 or Rain Shower"
          value={query}
          autoComplete="off"
          disabled={disabled}
          onFocus={() => {
            if (query.trim().length >= MIN_QUERY_LENGTH && (suggestions.length > 0 || loading || error)) {
              setShowSuggestions(true);
            }
          }}
          onChange={(e) => {
            setQuery(e.target.value);
            setShowSuggestions(true);
            setError('');
          }}
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              setShowSuggestions(false);
            }
          }}
        />
        <button
          type="submit"
          style={{
            padding: '0.7rem 1.4rem',
            borderRadius: '1rem',
            background: 'var(--primary-gradient)',
            color: 'var(--primary-color)',
            border: 'none',
            cursor: 'pointer',
            fontWeight: '900',
            fontSize: '0.85rem',
          }}
          disabled={loading || disabled}
        >
          {loading ? '...' : disabled ? 'VIEW' : 'ADD'}
        </button>
      </form>

      {typeof document !== 'undefined' && menuContent
        ? createPortal(menuContent, document.body)
        : null}
    </div>
  );
}
