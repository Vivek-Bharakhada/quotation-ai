import React from 'react';
import './website.css';

const FEATURE_LIST = [
  {
    title: 'Unified Catalog Brain',
    description:
      'Keep Aquant and Kohler price books searchable in one place with smart indexing and lightning-quick filters.',
  },
  {
    title: 'Quotation Generator',
    description:
      'Prepare branded PDFs in minutes with GST, staff selection, room summaries, and automatic numbering.',
  },
  {
    title: 'Works Everywhere',
    description:
      'Run in browser, install as a PWA, or package as a desktop app without changing your workflow.',
  },
  {
    title: 'Instant Sharing',
    description:
      'Send quotations directly on WhatsApp or email with secure, shareable PDF links.',
  },
];

const TIMELINE = [
  {
    step: '01',
    title: 'Upload Catalogs',
    description: 'Drop vendor PDFs once, sync them to the cloud, and keep them ready for every team member.',
  },
  {
    step: '02',
    title: 'Browse Collections',
    description: 'Jump through curated sections, pick finishes, and collect items into the quotation cart.',
  },
  {
    step: '03',
    title: 'Generate & Share',
    description: 'Create the PDF, preview instantly, and share with clients without leaving the app.',
  },
];

const NUMBERS = [
  { value: '2', label: 'Curated brand catalogs' },
  { value: '60s', label: 'Average quote preparation' },
  { value: '100%', label: 'Browser and app ready' },
];

export default function Website({ onEnterApp }) {
  return (
    <div className="website-shell">
      <header className="website-hero">
        <div className="website-hero-content">
          <span className="website-tag">Shreeji Ceramica Quotation Suite</span>
          <h1>Sell faster with quotations that feel premium.</h1>
          <p>
            One unified system for catalogs, pricing, quotations, and sharing. Designed for showroom teams
            who need speed without losing control.
          </p>
          <div className="website-hero-actions">
            <button className="website-btn primary" onClick={onEnterApp}>
              Enter App
            </button>
            <button
              className="website-btn ghost"
              onClick={() => {
                const target = document.getElementById('features');
                if (target) {
                  target.scrollIntoView({ behavior: 'smooth' });
                }
              }}
            >
              See Features
            </button>
          </div>
        </div>

        <div className="website-hero-card">
          <div className="hero-card-glow" />
          <div className="hero-card-content">
            <div className="hero-card-header">
              <div>
                <p className="hero-card-label">Live Snapshot</p>
                <h3>Quotation cockpit</h3>
              </div>
              <span className="hero-pill">Online</span>
            </div>
            <div className="hero-card-body">
              <div className="hero-line">
                <span>Client</span>
                <strong>Patel Residence</strong>
              </div>
              <div className="hero-line">
                <span>Rooms</span>
                <strong>4</strong>
              </div>
              <div className="hero-line">
                <span>Items</span>
                <strong>23</strong>
              </div>
              <div className="hero-total">
                <span>Grand Total</span>
                <strong>Rs 8,42,000</strong>
              </div>
            </div>
            <div className="hero-card-footer">
              <span>PDF ready in 52 seconds</span>
              <button className="hero-mini-btn" onClick={onEnterApp}>
                Open Now
              </button>
            </div>
          </div>
        </div>
      </header>

      <section className="website-metrics">
        {NUMBERS.map((item) => (
          <div key={item.label} className="metric-card">
            <strong>{item.value}</strong>
            <span>{item.label}</span>
          </div>
        ))}
      </section>

      <section id="features" className="website-features">
        <div className="section-heading">
          <p>Designed for teams who quote every day</p>
          <h2>Everything you need to move from catalog to customer faster.</h2>
        </div>

        <div className="feature-grid">
          {FEATURE_LIST.map((feature) => (
            <article key={feature.title} className="feature-card">
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
              <span className="feature-chip">Included</span>
            </article>
          ))}
        </div>
      </section>

      <section className="website-timeline">
        <div className="section-heading">
          <p>Workflow</p>
          <h2>From catalog upload to approved quotation in three steps.</h2>
        </div>
        <div className="timeline-grid">
          {TIMELINE.map((item) => (
            <div key={item.step} className="timeline-card">
              <span className="timeline-step">{item.step}</span>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="website-cta">
        <div>
          <h2>Ready to generate your next quotation?</h2>
          <p>Launch the app and prepare the first draft in under a minute.</p>
        </div>
        <button className="website-btn primary" onClick={onEnterApp}>
          Launch App
        </button>
      </section>
    </div>
  );
}
