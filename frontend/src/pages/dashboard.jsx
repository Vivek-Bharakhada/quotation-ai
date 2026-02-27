import React, { useMemo, useState } from 'react';
import axios from 'axios';
import './dashboard.css';

import BASE from '../api';


const AQUANT_INDEX = [
  { title: 'STONE WASH BASINS' },
  { title: 'ARTISTIC WASH BASINS IN UNIQUE MATERIALS' },
  { title: 'CERAMIC PEDESTAL WASH BASINS' },
  { title: 'CERAMIC BASINS IN WHITE & SPECIAL FINISHES' },
  { title: 'CERAMIC SANITARY WARE IN SPECIAL FINISHES' },
  { title: 'LIMITED EDITION SANITARY WARE IN SPECIAL FINISHES' },
  { title: 'CERAMIC BASINS IN SPECIAL FINISHES' },
  { title: 'CERAMIC WASH BASINS' },
  { title: 'INTELLIGENT SMART TOILET AQUANEXX SERIES' },
  { title: 'TOILETS' },
  { title: 'FLUSH TANKS/PLATES & URINAL SENSORS IN SPECIAL FINISHES' },
  { title: 'PRESTIGE COLLECTION BASIN MIXERS' },
  { title: 'FAUCETS & SHOWERING SYSTEMS IN SPECIAL FINISHES' },
  { title: 'SHOWERING SYSTEMS IN SPECIAL FINISHES' },
  { title: 'FAUCETS & SPOUTS IN SPECIAL FINISHES' },
  { title: 'SHOWERING SYSTEMS IN SPECIAL FINISHES' },
  { title: 'BODY JETS & BODY SHOWERS IN SPECIAL FINISHES' },
  { title: 'HAND SHOWERS IN SPECIAL FINISHES' },
  { title: 'BATH FITTINGS IN SPECIAL FINISHES' },
  { title: 'FAUCETS IN SPECIAL FINISHES' },
  { title: 'ALLIED PRODUCTS IN SPECIAL FINISHES' },
  { title: 'ACCESSORIES IN SPECIAL FINISHES' },
  { title: 'FAUCETS & SHOWERING SYSTEMS IN CHROME FINISH' },
  { title: 'FAUCETS IN CHROME FINISH' },
  { title: 'DIVERTERS & SHOWERING SYSTEMS IN CHROME & SPECIAL FINISH' },
  { title: 'CONCEALED CEILING MOUNTED SHOWERS IN CHROME FINISH' },
  { title: 'SHOWERS IN CHROME FINISH' },
  { title: 'BODY JETS & BODY SHOWERS IN CHROME FINISH' },
  { title: 'HAND SHOWERS & HEAD SHOWERS IN CHROME FINISH' },
  { title: 'ALLIED PRODUCTS IN CHROME FINISH' },
  { title: 'SS SHOWER PANELS IN MATT FINISH' },
  { title: 'KITCHEN FAUCETS IN SPECIAL & CHROME FINISH' },
  { title: 'FLOOR DRAINS IN CHROME & SPECIAL FINISHES' },
  { title: 'BATH COMPONENTS' },
  { title: 'OUR PROMISE' },
  { title: 'CARE INSTRUCTIONS' },
];

const KOHLER_INDEX = [
  { title: 'Toilets' },
  { title: 'Smart Toilets & Bidet Seats' },
  { title: '1 pc Toilets & Wall Hungs' },
  { title: 'In-Wall Tanks' },
  { title: 'Faceplates' },
  { title: 'Mirrors' },
  { title: 'Vanities' },
  { title: 'Wash Basins' },
  { title: 'Faucets' },
  { title: 'Showering' },
  { title: 'Steam' },
  { title: 'Shower Enclosures' },
  { title: 'Fittings' },
  { title: 'Accessories' },
  { title: 'Vibrant Finishes' },
  { title: 'French Gold' },
  { title: 'Brushed Bronze' },
  { title: 'Rose Gold' },
  { title: 'Matte Black' },
  { title: 'Brushed Rose Gold' },
  { title: 'Kitchen Sinks & Faucets' },
  { title: 'Bathtubs & Bath Fillers' },
  { title: 'Commercial Products' },
  { title: 'Cleaning Solutions' },
];

const BRAND_META = {
  Aquant: {
    subtitle: 'Contemporary Bathrooms',
    title: 'Price List 2025',
    heroImage:
      'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&q=80&w=2000',
  },
  Kohler: {
    subtitle: 'The Bold Look of Kohler',
    title: 'Price Book 2025',
    heroImage: '/kohler_cover.jpg',
  },
};

function toPriceLabel(rawPrice) {
  const parsed = Number(String(rawPrice ?? '').replace(/,/g, ''));
  if (Number.isFinite(parsed) && parsed > 0) {
    return `Rs ${parsed.toLocaleString()}`;
  }
  return 'MRP on request';
}

function buildSummary(text, name) {
  if (!text) {
    return 'Premium sanitaryware collection';
  }

  const lines = text
    .split('\n')
    .map((line) => line.trim())
    .filter(
      (line) =>
        line &&
        line.length > 4 &&
        line !== name &&
        !line.toLowerCase().includes('mrp') &&
        !line.toLowerCase().includes('sku code')
    );

  if (lines.length === 0) {
    return 'Premium sanitaryware collection';
  }

  return lines.slice(0, 2).join(' | ');
}

export default function Dashboard({ setCurrentPage, cart, setCart }) {
  const [activeBrand, setActiveBrand] = useState('Aquant');
  const [viewingCategory, setViewingCategory] = useState(null);
  const [categoryProducts, setCategoryProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [failedImages, setFailedImages] = useState({});

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [addForm, setAddForm] = useState({ name: '', price: '', image: null });

  const indexByBrand = useMemo(
    () => ({
      Aquant: AQUANT_INDEX,
      Kohler: KOHLER_INDEX,
    }),
    []
  );

  const currentBrandMeta = BRAND_META[activeBrand];
  const activeIndex = indexByBrand[activeBrand] || [];

  const handleBrandChange = (brand) => {
    setActiveBrand(brand);
    if (viewingCategory && viewingCategory.brand !== brand) {
      setViewingCategory(null);
      setCategoryProducts([]);
    }
  };

  const handleRefreshCatalog = async () => {
    setIsRefreshing(true);
    try {
      const res = await axios.get(`${BASE}/refresh`);
      alert(res.data.message || 'Indexing started. Please wait for completion.');
    } catch (error) {
      console.error(error);
      alert('Refresh failed. Please check backend status.');
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleCategoryClick = async (category, brand = activeBrand) => {
    setActiveBrand(brand);
    setViewingCategory({ name: category, brand });
    setLoadingProducts(true);

    try {
      const res = await axios.get(`${BASE}/catalog/browse`, {
        params: { brand, collection: category },
      });
      setCategoryProducts(res.data.results || []);
    } catch (error) {
      console.error(error);
      setCategoryProducts([]);
    } finally {
      setLoadingProducts(false);
    }
  };

  const markImageFailed = (src) => {
    if (!src) return;
    setFailedImages((prev) => (prev[src] ? prev : { ...prev, [src]: true }));
  };

  const handleAddChange = (event) => {
    const { name, value, files } = event.target;
    if (name === 'image') {
      setAddForm((prev) => ({ ...prev, image: files[0] || null }));
      return;
    }
    setAddForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleAddSubmit = async (event) => {
    event.preventDefault();
    if (!viewingCategory) {
      return;
    }

    setIsSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('name', addForm.name);
      formData.append('price', addForm.price);
      formData.append('brand', viewingCategory.brand);
      formData.append('category', viewingCategory.name);
      if (addForm.image) {
        formData.append('file', addForm.image);
      }

      await axios.post(`${BASE}/catalog/add`, formData);
      await handleCategoryClick(viewingCategory.name, viewingCategory.brand);
      setIsAddModalOpen(false);
      setAddForm({ name: '', price: '', image: null });
    } catch (error) {
      console.error(error);
      alert('Failed to add product.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const productCartId = (item) => {
    const brand = viewingCategory?.brand || activeBrand;
    return `${brand}|${item.name || 'item'}|${item.page || 0}|${item.price || 0}`;
  };

  const isInCart = (item) => cart.some((row) => row.id === productCartId(item));

  const addToCart = (item) => {
    const id = productCartId(item);
    if (cart.some((row) => row.id === id)) {
      return;
    }

    const newItem = {
      id,
      name: item.name || item.text?.split('\n')[0] || 'Unknown Product',
      price: item.price || '0',
      rawText: item.text || '',
      image: item.images && item.images.length > 0 ? item.images[0] : null,
    };

    setCart((prev) => [...prev, newItem]);
  };

  return (
    <div className={`db-root ${activeBrand === 'Aquant' ? 'brand-aquant' : 'brand-kohler'}`}>
      {!viewingCategory ? (
        <>
          <section
            className="db-hero"
            style={{
              backgroundImage: `url('${currentBrandMeta.heroImage}')`,
            }}
          >
            <div className="db-brand-switch" role="tablist" aria-label="Brand switch">
              {Object.keys(indexByBrand).map((brand) => (
                <button
                  key={brand}
                  className={`db-brand-btn ${activeBrand === brand ? 'active' : ''}`}
                  onClick={() => handleBrandChange(brand)}
                >
                  {brand}
                </button>
              ))}
            </div>

            <div className="db-hero-content">
              <p className="db-hero-subtitle">{currentBrandMeta.subtitle}</p>
              <h1>{activeBrand}</h1>
              <p className="db-hero-title">{currentBrandMeta.title}</p>
            </div>

            <div className="db-hero-actions">
              <button className="db-btn db-btn-light" onClick={() => setCurrentPage('search')}>
                Open Search
              </button>
              <button className="db-btn db-btn-light" onClick={() => setCurrentPage('quotation')}>
                Create Quotation ({cart.length})
              </button>
              <button
                className="db-btn db-btn-primary"
                onClick={handleRefreshCatalog}
                disabled={isRefreshing}
              >
                {isRefreshing ? 'Refreshing...' : 'Refresh Catalog Data'}
              </button>
            </div>
          </section>

          <section className="db-index-layout">
            <article className="db-index-card">
              <header className="db-index-head">
                <h2>{activeBrand} Catalog Directory</h2>
                <p>Select a section to browse products and pricing.</p>
              </header>

              <div className="db-index-grid">
                {activeIndex.map((section) => (
                  <button
                    key={`${activeBrand}-${section.title}`}
                    className="db-index-row"
                    onClick={() => handleCategoryClick(section.title, activeBrand)}
                  >
                    <span className="db-index-arrow">-&gt;</span>
                    <span className="db-index-label">{section.title}</span>
                  </button>
                ))}
              </div>
            </article>

            <aside className="db-helper-card">
              <h3>Workflow</h3>
              <ol>
                <li>Choose brand and section from the directory.</li>
                <li>Review products and add required lines to quotation cart.</li>
                <li>Move to quotation page and generate PDF.</li>
              </ol>

              <div className="db-helper-stats">
                <div>
                  <span>Sections</span>
                  <strong>{activeIndex.length}</strong>
                </div>
                <div>
                  <span>In Cart</span>
                  <strong>{cart.length}</strong>
                </div>
              </div>

              <button className="db-btn db-btn-primary full" onClick={() => setCurrentPage('quotation')}>
                Go To Quotation
              </button>
            </aside>
          </section>
        </>
      ) : (
        <section className="db-browse-shell">
          <div className="db-topbar">
            <button
              className="db-btn db-btn-light"
              onClick={() => {
                setViewingCategory(null);
                setCategoryProducts([]);
              }}
            >
              Back To Index
            </button>

            <div className="db-topbar-actions">
              <button className="db-btn db-btn-light" onClick={() => setCurrentPage('quotation')}>
                Quotation ({cart.length})
              </button>
              <button className="db-btn db-btn-primary" onClick={() => setIsAddModalOpen(true)}>
                Add Missing Product
              </button>
            </div>
          </div>

          <div className="db-browse-layout">
            <aside className="db-side-index">
              <h3>{activeBrand} Index</h3>
              <div className="db-side-list">
                {activeIndex.map((section) => (
                  <button
                    key={`${activeBrand}-side-${section.title}`}
                    className={`db-side-item ${viewingCategory.name === section.title ? 'active' : ''}`}
                    onClick={() => handleCategoryClick(section.title, activeBrand)}
                  >
                    {section.title}
                  </button>
                ))}
              </div>
            </aside>

            <article className="db-products-panel">
              <header className="db-products-header">
                <span className="db-chip">{viewingCategory.brand}</span>
                <h2>{viewingCategory.name}</h2>
                <p>
                  {loadingProducts
                    ? 'Loading products...'
                    : `${categoryProducts.length} item${categoryProducts.length === 1 ? '' : 's'} available`}
                </p>
              </header>

              {loadingProducts ? (
                <div className="db-loading-wrap">
                  <div className="db-loader" />
                  <p>Fetching products...</p>
                </div>
              ) : categoryProducts.length > 0 ? (
                <div className="db-products-grid">
                  {categoryProducts.map((item, idx) => {
                    const alreadyAdded = isInCart(item);
                    const imageCandidates = (item.images || []).filter(Boolean).map((p) => `${BASE}${p}`);
                    const imageSrc = imageCandidates.find((src) => !failedImages[src]) || '';
                    const hasImage = imageSrc && !failedImages[imageSrc];

                    return (
                      <div key={`${item.name || 'item'}-${idx}`} className="db-product-card">
                        <div className="db-product-image-wrap">
                          {hasImage ? (
                            <img src={imageSrc} alt={item.name || 'Product'} onError={() => markImageFailed(imageSrc)} />
                          ) : (
                            <div className="db-no-image">IMAGE NOT FOUND</div>
                          )}
                        </div>

                        <div className="db-product-body">
                          <h3>{item.name || 'Unnamed Product'}</h3>
                          <p>{buildSummary(item.text, item.name)}</p>

                          <div className="db-product-footer">
                            <span>{toPriceLabel(item.price)}</span>
                            <button
                              className={`db-card-btn ${alreadyAdded ? 'added' : ''}`}
                              onClick={() => addToCart(item)}
                              disabled={alreadyAdded}
                            >
                              {alreadyAdded ? 'Added' : 'Add To Quote'}
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="db-empty-state">
                  <h4>No products found for this section.</h4>
                  <p>Try refreshing catalog data or use Add Missing Product.</p>
                </div>
              )}
            </article>
          </div>
        </section>
      )}

      {isAddModalOpen && (
        <div className="db-modal-overlay">
          <div className="db-modal" role="dialog" aria-modal="true">
            <button className="db-modal-close" onClick={() => setIsAddModalOpen(false)}>
              x
            </button>

            <h2>Add Product to {viewingCategory?.name || activeBrand}</h2>

            <form onSubmit={handleAddSubmit}>
              <label>
                Product Name and Code
                <input
                  required
                  name="name"
                  value={addForm.name}
                  onChange={handleAddChange}
                  placeholder="Example: K-12345 Product Name"
                />
              </label>

              <label>
                MRP Price
                <input
                  required
                  type="number"
                  name="price"
                  value={addForm.price}
                  onChange={handleAddChange}
                  placeholder="Example: 15000"
                />
              </label>

              <label>
                Product Image (Optional)
                <input type="file" name="image" accept="image/*" onChange={handleAddChange} />
              </label>

              <button type="submit" className="db-btn db-btn-primary full" disabled={isSubmitting}>
                {isSubmitting ? 'Saving...' : 'Save Product'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
