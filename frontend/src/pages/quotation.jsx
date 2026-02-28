import { useState, useEffect } from 'react';
import axios from 'axios';
import './quotation.css';

import BASE from '../api';


export default function Quotation({ cart }) {
  const [client, setClient] = useState({
    client_name: '',
    mobile: '',
    email: '',
    company: '',
    gst: '',
    address: '',
  });

  const [showGstInput, setShowGstInput] = useState(false);

  const [items, setItems] = useState(
    cart && cart.length > 0
      ? cart.map((c) => ({
        name: c.name,
        price: c.price || '0',
        quantity: 1,
        discount: 0,
        image: c.image || null,
        rawText: c.rawText || '',
      }))
      : [{ name: '', price: '', quantity: 1, discount: 0, image: null, rawText: '' }]
  );

  const [discountPercent, setDiscountPercent] = useState(0);
  const [gstRate, setGstRate] = useState(18);
  const [quoteHistory, setQuoteHistory] = useState([]);
  const [generatedPdfUrl, setGeneratedPdfUrl] = useState(null);
  const [generatedPdfServerUrl, setGeneratedPdfServerUrl] = useState('');
  const [generatedPdfServerName, setGeneratedPdfServerName] = useState('');
  const [quoteNumber, setQuoteNumber] = useState('');
  const [quoteDate, setQuoteDate] = useState('');

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${BASE}/list-quotes`);
      setQuoteHistory(res.data.quotes || []);
    } catch (err) {
      console.error('Failed to fetch history', err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const loadQuote = async (id) => {
    try {
      const res = await axios.get(`${BASE}/get-quote/${id}`);
      const data = res.data;
      setClient({
        client_name: data.client_name || '',
        mobile: data.mobile || '',
        email: data.email || '',
        company: data.company || '',
        gst: data.gst || '',
        address: data.address || '',
      });
      setItems(data.items || []);
      setDiscountPercent(data.discount_percent || 0);
      setGstRate(data.gst_rate || 18);
      if (data.gst) setShowGstInput(true);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      alert('Failed to load quotation');
    }
  };

  const deleteQuote = async (id) => {
    if (!window.confirm('Delete this quotation record?')) return;
    try {
      await axios.delete(`${BASE}/delete-quote/${id}`);
      fetchHistory();
    } catch (err) {
      alert('Delete failed');
    }
  };

  const handleClientChange = (e) => {
    setClient({ ...client, [e.target.name]: e.target.value });
  };

  const handleItemChange = (index, e) => {
    const newItems = [...items];
    newItems[index][e.target.name] = e.target.value;
    setItems(newItems);
  };

  const addItem = () => {
    setItems([...items, { name: '', price: '', quantity: 1, discount: 0, image: null, rawText: '' }]);
  };

  const removeItem = (index) => {
    const newItems = items.filter((_, i) => i !== index);
    setItems(
      newItems.length > 0
        ? newItems
        : [{ name: '', price: '', quantity: 1, discount: 0, image: null, rawText: '' }]
    );
  };

  const subtotal = items.reduce((sum, item) => {
    const qty = parseInt(item.quantity, 10) || 1;
    const price = parseFloat(item.price) || 0;
    const disc = parseFloat(item.discount) || 0;
    const total = price * qty;
    return sum + (total - (total * disc) / 100);
  }, 0);

  const discountAmount = subtotal * (parseFloat(discountPercent || 0) / 100);
  const taxableAmount = subtotal - discountAmount;
  const gstAmount = taxableAmount * (parseFloat(gstRate || 0) / 100);
  const grandTotal = taxableAmount + gstAmount;
  const quoteFilename = `Quotation_${(client.client_name || 'Client').replace(/\s+/g, '_')}.pdf`;

  const formatMoney = (value) => {
    const num = Number(value || 0);
    return `Rs ${num.toFixed(2)}`;
  };

  const getItemTotal = (item) => {
    const qty = parseFloat(item.quantity) || 1;
    const price = parseFloat(item.price) || 0;
    const disc = parseFloat(item.discount) || 0;
    const gross = qty * price;
    return gross - (gross * disc) / 100;
  };

  const buildDetailedShareText = () => {
    const lines = [];
    lines.push(`Quotation for ${client.client_name || 'Customer'}`);
    if (client.company) lines.push(`Company: ${client.company}`);
    if (client.mobile) lines.push(`Mobile: ${client.mobile}`);
    if (client.email) lines.push(`Email: ${client.email}`);
    if (client.address) lines.push(`Address: ${client.address}`);
    if (client.gst) lines.push(`GSTIN: ${client.gst}`);
    lines.push('');
    lines.push('Items:');
    items.forEach((item, index) => {
      const name = item.name || `Item ${index + 1}`;
      const qty = parseFloat(item.quantity) || 1;
      const price = parseFloat(item.price) || 0;
      const disc = parseFloat(item.discount) || 0;
      const lineTotal = getItemTotal(item);
      lines.push(
        `${index + 1}. ${name} | Qty: ${qty} | Price: ${formatMoney(price)} | Disc: ${disc}% | Total: ${formatMoney(lineTotal)}`
      );
    });
    lines.push('');
    lines.push(`Subtotal: ${formatMoney(subtotal)}`);
    lines.push(`Discount: ${parseFloat(discountPercent || 0)}% (${formatMoney(discountAmount)})`);
    lines.push(`Taxable Amount: ${formatMoney(taxableAmount)}`);
    lines.push(`GST (${parseFloat(gstRate || 0)}%): ${formatMoney(gstAmount)}`);
    lines.push(`Grand Total: ${formatMoney(grandTotal)}`);
    return lines.join('\n');
  };

  const getPdfFile = async () => {
    const response = await fetch(generatedPdfUrl);
    const blob = await response.blob();
    return new File([blob], generatedPdfServerName || quoteFilename, { type: 'application/pdf' });
  };

  const downloadGeneratedPdf = () => {
    const link = document.createElement('a');
    link.href = generatedPdfUrl;
    link.download = generatedPdfServerName || quoteFilename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getWhatsappNumber = () => {
    const mobileRaw = String(client.mobile || '').trim();
    const mobileDigits = mobileRaw.replace(/\D/g, '');
    if (mobileDigits.length === 10) return `91${mobileDigits}`;
    if (mobileDigits.length === 11 && mobileDigits.startsWith('0')) return `91${mobileDigits.slice(1)}`;
    if (mobileDigits.length >= 12 && mobileDigits.startsWith('91')) return mobileDigits;
    return '';
  };

  const generatePDF = async () => {
    try {
      const payload = {
        ...client,
        items,
        discount_percent: parseFloat(discountPercent || 0),
        gst_rate: parseFloat(gstRate || 0),
        subtotal,
        discount_amount: discountAmount,
        taxable_amount: taxableAmount,
        gst_amount: gstAmount,
        grand_total: grandTotal,
      };

      const response = await axios.post(`${BASE}/generate-quote`, payload, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      setGeneratedPdfUrl(url);
      const serverPath = response.headers['x-quote-file-url'] || '';
      const serverName = response.headers['x-quote-file-name'] || '';
      const qNum = response.headers['x-quote-number'] || '';
      setGeneratedPdfServerUrl(serverPath ? `${BASE}${serverPath}` : '');
      setGeneratedPdfServerName(serverName || '');
      setQuoteNumber(qNum);
      const today = new Date();
      setQuoteDate(today.toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' }));
      fetchHistory();
    } catch (error) {
      console.error('Error generating PDF', error);
      alert('Failed to generate PDF');
    }
  };

  const handleSystemShare = async () => {
    if (!generatedPdfUrl) return;

    try {
      const file = await getPdfFile();
      const shareMessage = buildDetailedShareText();

      const shareData = {
        title: `Quotation from ${client.company || 'Our Company'}`,
        text: shareMessage,
        files: [file],
      };

      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share(shareData);
      } else {
        downloadGeneratedPdf();
        alert('System file share not supported on this browser. PDF downloaded, please share manually.');
      }
    } catch (error) {
      console.error('Error sharing file:', error);
    }
  };

  const handleWhatsAppShare = async () => {
    if (!generatedPdfUrl) return;
    try {
      const whatsappNumber = getWhatsappNumber();
      
      const itemLines = items.map((item, i) => {
        const qty = parseFloat(item.quantity) || 1;
        const price = parseFloat(item.price) || 0;
        const disc = parseFloat(item.discount) || 0;
        const total = getItemTotal(item);
        return `  ${i + 1}. ${item.name || `Item ${i + 1}`} (${qty}x) → ₹${price.toLocaleString('en-IN')} | Disc: ${disc}% | Total: ₹${total.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
      }).join('\n');

      // FULL QUOTATION DETAILS
      const fullMsg = [
        `🏢 *SHREEJI CERAMICA*`,
        `Redefining Luxury | Ph: 9033745455`,
        `═══════════════════════════════════`,
        ``,
        `📋 *QUOTATION*`,
        `Quotation #: ${quoteNumber || 'N/A'}`,
        `Date: ${quoteDate || new Date().toLocaleDateString('en-IN')}`,
        ``,
        `👤 *CLIENT INFORMATION*`,
        `Name: ${client.client_name || 'N/A'}`,
        client.mobile ? `Mobile: ${client.mobile}` : null,
        client.company ? `Company: ${client.company}` : null,
        client.address ? `Address: ${client.address}` : null,
        client.gst ? `GSTIN: ${client.gst}` : null,
        ``,
        `📦 *ITEMS*`,
        itemLines,
        ``,
        `💰 *FINANCIAL BREAKDOWN*`,
        `Subtotal: ₹${subtotal.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`,
        discountAmount > 0 ? `Discount (${discountPercent}%): -₹${discountAmount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : null,
        `Taxable Amount: ₹${taxableAmount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`,
        gstAmount > 0 ? `GST (${gstRate}%): +₹${gstAmount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : null,
        ``,
        `*🎯 GRAND TOTAL: ₹${grandTotal.toLocaleString('en-IN', { maximumFractionDigits: 2 })}*`,
        ``,
        `📄 PDF: ${generatedPdfServerUrl}`,
        ``,
        `Thank you! 🙏`,
        `www.shreejiceramica.com`,
      ].filter(l => l !== null).join('\n');

      const waUrl = whatsappNumber
        ? `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(fullMsg)}`
        : `https://wa.me/?text=${encodeURIComponent(fullMsg)}`;

      window.open(waUrl, '_blank', 'noopener,noreferrer');
    } catch (error) {
      console.error('Error sharing on WhatsApp:', error);
      alert('Unable to open WhatsApp share.');
    }
  };

  const handleWhatsAppAPIShare = async () => {
    if (!generatedPdfUrl || !generatedPdfServerUrl) {
      alert('PDF not ready. Please generate PDF first.');
      return;
    }

    try {
      const whatsappNumber = getWhatsappNumber();

      // ONLY PDF MESSAGE
      const pdfMsg = [
        `📄 *PDF QUOTATION*`,
        ``,
        `Quotation: ${quoteNumber || 'N/A'}`,
        `Date: ${quoteDate || new Date().toLocaleDateString('en-IN')}`,
        `Client: ${client.client_name || 'Customer'}`,
        `Total: ₹${grandTotal.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`,
        ``,
        `📥 Download PDF:`,
        `${generatedPdfServerUrl}`,
      ].join('\n');

      const waUrl = whatsappNumber
        ? `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(pdfMsg)}`
        : `https://wa.me/?text=${encodeURIComponent(pdfMsg)}`;

      window.open(waUrl, '_blank', 'noopener,noreferrer');
    } catch (error) {
      console.error('Error sharing PDF on WhatsApp:', error);
      alert('Unable to open WhatsApp share.');
    }
  };

  const handleEmailShare = async () => {
    if (!generatedPdfUrl) return;
    try {
      const recipient = String(client.email || '').trim();
      if (!recipient) {
        alert('Please enter client email ID before sending email.');
        return;
      }

      const pdfLink = generatedPdfServerUrl || '';
      const subject = `Quotation ${quoteNumber} — Shreeji Ceramica`;
      const body = [
        `Dear ${client.client_name || 'Customer'},`,
        ``,
        `Thank you for your interest in Shreeji Ceramica — Redefining Luxury.`,
        ``,
        `Please find your quotation details below:`,
        ``,
        `Quotation No : ${quoteNumber || 'N/A'}`,
        `Date         : ${quoteDate || new Date().toLocaleDateString('en-IN')}`,
        client.company ? `Company      : ${client.company}` : null,
        client.address ? `Address      : ${client.address}` : null,
        client.gst ? `GSTIN        : ${client.gst}` : null,
        ``,
        `Items:`,
        ...items.map((item, i) => {
          const qty = parseFloat(item.quantity) || 1;
          const price = parseFloat(item.price) || 0;
          const disc = parseFloat(item.discount) || 0;
          const total = getItemTotal(item);
          return `${i + 1}. ${item.name || `Item ${i + 1}`} | Qty: ${qty} | Rs ${price.toLocaleString('en-IN')} | Disc: ${disc}% | Total: Rs ${total.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
        }),
        ``,
        `Subtotal      : Rs ${subtotal.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`,
        discountAmount > 0 ? `Discount (${discountPercent}%) : -Rs ${discountAmount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : null,
        `Taxable Amount: Rs ${taxableAmount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`,
        gstAmount > 0 ? `GST (${gstRate}%)    : +Rs ${gstAmount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : null,
        `Grand Total   : Rs ${grandTotal.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`,
        ``,
        pdfLink ? `Download PDF: ${pdfLink}` : null,
        ``,
        `For any queries, contact us at:`,
        `Phone : 9033745455`,
        `Email : shreejiceramica303@gmail.com`,
        `Web   : www.shreejiceramica.com`,
        ``,
        `Warm regards,`,
        `Shreeji Ceramica Team`,
      ].filter(l => l !== null).join('\n');

      // Try Gmail compose URL first (opens Gmail in browser directly)
      const gmailUrl = `https://mail.google.com/mail/?view=cm&to=${encodeURIComponent(recipient)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      window.open(gmailUrl, '_blank', 'noopener,noreferrer');
    } catch (error) {
      console.error('Error sharing on Email:', error);
      alert('Unable to open Gmail.');
    }
  };

  return (
    <div className="qt-root">
      <header className="qt-header">
        <h2>Create New Quotation</h2>
      </header>

      <section className="qt-client-grid">
        <input
          className="qt-field"
          name="client_name"
          value={client.client_name}
          placeholder="Client Name"
          onChange={handleClientChange}
        />
        <input
          className="qt-field"
          name="mobile"
          value={client.mobile}
          placeholder="Mobile Number"
          onChange={handleClientChange}
        />
        <input
          className="qt-field"
          name="company"
          value={client.company}
          placeholder="Company Name"
          onChange={handleClientChange}
        />
        <input
          className="qt-field"
          type="email"
          name="email"
          value={client.email}
          placeholder="Email ID"
          onChange={handleClientChange}
        />

        <div className="qt-span-2">
          <input
            className="qt-field"
            name="address"
            value={client.address}
            placeholder="Address"
            onChange={handleClientChange}
          />
        </div>

        {showGstInput ? (
          <input
            className="qt-field"
            name="gst"
            value={client.gst}
            placeholder="Client GSTIN"
            autoFocus
            onChange={handleClientChange}
          />
        ) : (
          <button className="qt-gst-btn" onClick={() => setShowGstInput(true)}>
            + Add GSTIN Detail
          </button>
        )}
      </section>

      <section className="qt-items-section">
        <div className="qt-items-head">
          <h3>Itemized List</h3>
          <button onClick={addItem} className="qt-add-row">
            + Add Row
          </button>
        </div>

        <div className="qt-items-list">
          {items.map((item, index) => (
            <article key={index} className="qt-item-card">
              <div className="qt-item-grid">
                <div className="qt-thumb">
                  {item.image ? (
                    <img src={`${BASE}${item.image}`} alt="thumb" />
                  ) : (
                    <div className="qt-no-thumb">NO IMG</div>
                  )}
                </div>

                <input
                  className="qt-field qt-name-field"
                  name="name"
                  value={item.name}
                  placeholder="Item Name"
                  onChange={(e) => handleItemChange(index, e)}
                />
                <input
                  className="qt-field"
                  name="price"
                  type="number"
                  value={item.price}
                  placeholder="Price"
                  onChange={(e) => handleItemChange(index, e)}
                />
                <input
                  className="qt-field"
                  name="quantity"
                  type="number"
                  value={item.quantity}
                  placeholder="Qty"
                  onChange={(e) => handleItemChange(index, e)}
                />
                <input
                  className="qt-field"
                  name="discount"
                  type="number"
                  value={item.discount}
                  placeholder="Disc %"
                  onChange={(e) => handleItemChange(index, e)}
                />

                <button className="qt-remove-btn" onClick={() => removeItem(index)}>
                  x
                </button>
              </div>

              <div className="qt-detail-wrap">
                <textarea
                  className="qt-detail-area"
                  name="rawText"
                  value={item.rawText}
                  placeholder="Complete item details (specifications, size, etc.)"
                  onChange={(e) => handleItemChange(index, e)}
                />
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="qt-summary">
        <h4>Financial Summary</h4>

        <div className="qt-summary-row">
          <span>Subtotal</span>
          <strong>Rs {subtotal.toFixed(2)}</strong>
        </div>

        <div className="qt-summary-row">
          <span>Extra Discount (%)</span>
          <input
            className="qt-mini-input"
            type="number"
            min="0"
            max="100"
            value={discountPercent}
            onChange={(e) => setDiscountPercent(e.target.value)}
          />
        </div>

        <div className="qt-summary-row">
          <span>GST Rate (%)</span>
          <select className="qt-mini-select" value={gstRate} onChange={(e) => setGstRate(e.target.value)}>
            {[0, 5, 12, 18, 28].map((r) => (
              <option key={r} value={r}>
                {r}%
              </option>
            ))}
          </select>
        </div>

        <div className="qt-summary-row gst">
          <span>Estimated GST</span>
          <strong>+ Rs {gstAmount.toFixed(2)}</strong>
        </div>

        <div className="qt-total-row">
          <span>Grand Total</span>
          <strong>Rs {grandTotal.toFixed(2)}</strong>
        </div>

        {!generatedPdfUrl ? (
          <button onClick={generatePDF} className="qt-generate-btn">
            GENERATE PDF
          </button>
        ) : (
          <div className="qt-pdf-actions">
            {/* Quote number badge */}
            {quoteNumber && (
              <div className="qt-quote-info">
                <span className="qt-quote-num">🔖 {quoteNumber}</span>
                <span className="qt-quote-dt">📅 {quoteDate}</span>
              </div>
            )}

            <div className="qt-pdf-links">
              <a href={generatedPdfUrl} target="_blank" rel="noreferrer" className="qt-pdf-view">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg>
                View PDF
              </a>
              <a href={generatedPdfUrl} download={generatedPdfServerName || quoteFilename} className="qt-pdf-download">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
                Download PDF
              </a>
            </div>

            <div className="qt-share-row">
              <button onClick={handleWhatsAppAPIShare} className="qt-share-btn qt-wa-btn qt-wa-api-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg>
                PDF Only <span className="qt-pdf-badge">Link</span>
              </button>
              <button onClick={handleEmailShare} className="qt-share-btn qt-gmail-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 010 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.910 1.528-1.145C21.69 2.28 24 3.434 24 5.457z" /></svg>
                Send Gmail
              </button>
            </div>

            <div className="qt-share-row-alt">
              <button onClick={handleWhatsAppShare} className="qt-share-btn qt-wa-btn-chat">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg>
                Full Details
              </button>
              <button onClick={handleSystemShare} className="qt-share-btn qt-system-btn">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" /><line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" /></svg>
                Share More
              </button>
            </div>

            <button
              onClick={() => {
                setGeneratedPdfUrl(null);
                setGeneratedPdfServerUrl('');
                setGeneratedPdfServerName('');
                setQuoteNumber('');
                setQuoteDate('');
              }}
              className="qt-edit-btn"
            >
              ✏️ Edit Again
            </button>
          </div>
        )}
      </section>

      <section className="qt-history">
        <div className="qt-history-line" />
        <h3 className="qt-history-title">
          Past Records
          <span>{quoteHistory.length} files</span>
        </h3>

        {quoteHistory.length > 0 ? (
          <div className="qt-history-grid">
            {quoteHistory.map((q) => (
              <article key={q.id} className="qt-record-card">
                <div className="qt-record-head">
                  <div className="qt-record-meta">
                    <div className="qt-record-client">{q.client}</div>
                    <div className="qt-record-time">
                      {new Date(q.date * 1000).toLocaleDateString()} {' | '}
                      {new Date(q.date * 1000).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                  </div>
                  <div className="qt-record-total">Rs {q.total.toLocaleString()}</div>
                </div>

                <div className="qt-record-actions">
                  <button onClick={() => loadQuote(q.id)} className="qt-resume-btn">
                    RESUME EDIT
                  </button>
                  <button onClick={() => deleteQuote(q.id)} className="qt-delete-btn">
                    Delete
                  </button>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="qt-history-empty">
            <p>
              No quotation records found yet.
              <br />
              Generate your first bill to start history tracking.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
