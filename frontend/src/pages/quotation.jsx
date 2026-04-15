import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import './quotation.css';

import BASE from '../api';
import InlineSearch from './InlineSearch';
import { readJson, writeJson } from '../utils/storage';
import { resolveAssetUrl } from '../utils/url';

const QUOTE_DRAFT_KEY = 'quotation-ai/quote-draft';
const QUOTE_HISTORY_CACHE_KEY = 'quotation-ai/quote-history-cache';
const DEFAULT_ROOM_OPTIONS = [
  'Master Bath',
  'Common Bath',
  'Guest Bath',
  'Powder Room',
  'Kitchen',
  'Utility',
  'Balcony',
  'Living Room',
];

const blankClient = {
  client_name: '',
  mobile: '',
  email: '',
  company: '',
  gst: '',
  address: '',
};

const createBlankItem = () => ({
  name: '',
  room: '',
  price: '',
  quantity: 1,
  discount: 0,
  image: null,
  rawText: '',
  sku: '',
  size: '',
});

const mapCartToItems = (cart = []) =>
  cart && cart.length > 0
    ? cart.map((item) => ({
        name: item.name,
        price: item.price || '0',
        quantity: 1,
        discount: 0,
        image: item.image || null,
        room: '',
        rawText: item.rawText || item.text || '',
        sku: item.sku || '',
        size: item.size || '',
      }))
    : [createBlankItem()];

const normalizeQuoteHistory = (value) => (Array.isArray(value) ? value : []);

async function notifyQuoteReady(quoteNumber, grandTotal) {
  if (typeof window === 'undefined' || !('Notification' in window) || Notification.permission !== 'granted') {
    return;
  }

  const numericTotal = Number(grandTotal || 0);
  const title = quoteNumber ? `Quotation ${quoteNumber} ready` : 'Quotation ready';
  const body = Number.isFinite(numericTotal) && numericTotal > 0
    ? `PDF generated successfully. Grand total: Rs ${numericTotal.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
    : 'Your quotation PDF is ready to view and share.';

  if ('serviceWorker' in navigator) {
    const registration = await navigator.serviceWorker.getRegistration();
    if (registration) {
      registration.showNotification(title, {
        body,
        icon: '/logo192.png',
        badge: '/logo192.png',
      });
      return;
    }
  }

  new Notification(title, { body, icon: '/logo192.png' });
}

function RoomCombobox({ value, options, placeholder, onValueChange }) {
  const [isOpen, setIsOpen] = useState(false);
  const [menuPlacement, setMenuPlacement] = useState('down');
  const [menuStyle, setMenuStyle] = useState(null);
  const wrapperRef = useRef(null);
  const inputRef = useRef(null);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      const clickedInsideField = wrapperRef.current && wrapperRef.current.contains(event.target);
      const clickedInsideMenu = menuRef.current && menuRef.current.contains(event.target);

      if (!clickedInsideField && !clickedInsideMenu) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const currentValue = value || '';
  const normalizedValue = currentValue.trim().toLowerCase();
  const filteredOptions = options.filter((option) =>
    option.toLowerCase().includes(normalizedValue)
  );
  const hasExactMatch = options.some((option) => option.toLowerCase() === normalizedValue);
  const canUseTypedValue = currentValue.trim() && !hasExactMatch;

  const commitValue = (nextValue) => {
    onValueChange(nextValue);
    setIsOpen(false);
    requestAnimationFrame(() => inputRef.current?.focus());
  };

  useEffect(() => {
    if (!isOpen || !wrapperRef.current) {
      return;
    }

    const updateMenuPosition = () => {
      if (!wrapperRef.current) {
        return;
      }

      const wrapperRect = wrapperRef.current.getBoundingClientRect();
      const menuHeight = Math.min(menuRef.current?.scrollHeight || 220, 220);
      const spaceBelow = window.innerHeight - wrapperRect.bottom;
      const spaceAbove = wrapperRect.top;
      const nextPlacement = spaceBelow < menuHeight + 24 && spaceAbove > spaceBelow ? 'up' : 'down';
      const viewportPadding = 16;
      const nextWidth = Math.min(
        Math.max(wrapperRect.width, 220),
        window.innerWidth - viewportPadding * 2
      );
      const nextLeft = Math.min(
        Math.max(wrapperRect.left, viewportPadding),
        window.innerWidth - viewportPadding - nextWidth
      );
      const nextTop = nextPlacement === 'up'
        ? Math.max(viewportPadding, wrapperRect.top - menuHeight - 8)
        : Math.min(window.innerHeight - viewportPadding - menuHeight, wrapperRect.bottom + 8);

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
  }, [isOpen, currentValue, options]);

  const menuContent = isOpen && (filteredOptions.length > 0 || canUseTypedValue) ? (
    <div
      ref={menuRef}
      className={`qt-room-combobox-menu ${menuPlacement === 'up' ? 'open-up' : ''}`}
      style={menuStyle || undefined}
    >
      {canUseTypedValue && (
        <button
          type="button"
          className="qt-room-combobox-option qt-room-combobox-option-create"
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => commitValue(currentValue.trim())}
        >
          Use "{currentValue.trim()}"
        </button>
      )}

      {filteredOptions.map((option) => (
        <button
          key={option}
          type="button"
          className={`qt-room-combobox-option ${option === currentValue ? 'active' : ''}`}
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => commitValue(option)}
        >
          {option}
        </button>
      ))}
    </div>
  ) : null;

  return (
    <div
      ref={wrapperRef}
      className={`qt-room-combobox ${isOpen ? 'open' : ''} ${menuPlacement === 'up' ? 'open-up' : ''}`}
    >
      <input
        ref={inputRef}
        className="qt-field qt-room-field"
        name="room"
        value={currentValue}
        placeholder={placeholder}
        autoComplete="off"
        onChange={(e) => {
          onValueChange(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        onKeyDown={(e) => {
          if (e.key === 'ArrowDown') {
            e.preventDefault();
            setIsOpen(true);
          }
          if (e.key === 'Escape') {
            setIsOpen(false);
          }
        }}
      />
      <button
        type="button"
        className="qt-room-combobox-toggle"
        aria-label="Show room suggestions"
        onMouseDown={(e) => e.preventDefault()}
        onClick={() => {
          setIsOpen((previous) => !previous);
          inputRef.current?.focus();
        }}
      >
        <span className="qt-room-combobox-caret" />
      </button>

      {typeof document !== 'undefined' && menuContent ? createPortal(menuContent, document.body) : null}
    </div>
  );
}


export default function Quotation({ cart }) {
  // We no longer restore the draft on mount to ensure the page feels fresh on reload
  const [client, setClient] = useState(blankClient);
  const [showGstInput, setShowGstInput] = useState(false);
  const [items, setItems] = useState(() => mapCartToItems(cart));
  const [discountPercent, setDiscountPercent] = useState(0);
  const [gstRate, setGstRate] = useState(18);
  const [quoteHistory, setQuoteHistory] = useState(() => normalizeQuoteHistory(readJson(QUOTE_HISTORY_CACHE_KEY, [])));
  const [generatedPdfUrl, setGeneratedPdfUrl] = useState(null);
  const [generatedPdfServerUrl, setGeneratedPdfServerUrl] = useState('');
  const [generatedPdfServerName, setGeneratedPdfServerName] = useState('');
  const [quoteNumber, setQuoteNumber] = useState('');
  const [quoteDate, setQuoteDate] = useState('');
  const [showBgLogo, setShowBgLogo] = useState(false);
  const [madeBy, setMadeBy] = useState('');
  const [madeByPhone, setMadeByPhone] = useState('');
  const [madeByEmail, setMadeByEmail] = useState('');
  const [isOffline, setIsOffline] = useState(() => (typeof navigator === 'undefined' ? false : !navigator.onLine));
  const [notificationPermission, setNotificationPermission] = useState(() =>
    typeof window !== 'undefined' && 'Notification' in window ? Notification.permission : 'default'
  );
  const [historySearchTerm, setHistorySearchTerm] = useState('');

  const customRoomOptions = Array.from(
    new Set(
      items
        .map((item) => (item.room || '').trim())
        .filter(Boolean)
    )
  )
    .filter(
      (roomName) =>
        !DEFAULT_ROOM_OPTIONS.some(
          (defaultOption) => defaultOption.toLowerCase() === roomName.toLowerCase()
        )
    )
    .sort((a, b) => a.localeCompare(b));

  const roomOptions = [...DEFAULT_ROOM_OPTIONS, ...customRoomOptions];

  const staffOptions = [
    { name: 'Harsh Bhai', phone: '+91 82385 21277' },
    { name: 'Karan Bhai', phone: '+91 82009 17069' },
    { name: 'Kunal Bhai', phone: '+91 98987 13167' },
  ];

  const handleStaffSelect = (e) => {
    const val = e.target.value;
    if (!val) {
      setMadeBy('');
      setMadeByPhone('');
      return;
    }
    const staff = staffOptions.find(s => s.name === val);
    if (staff) {
      setMadeBy(staff.name);
      setMadeByPhone(staff.phone);
    }
  };

  // Keyboard shortcut for Catalog Sync removed per user request to allow standard browser hard refresh

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${BASE}/list-quotes`);
      const normalized = res.data.quotes || [];
      setQuoteHistory(normalized);
      writeJson(QUOTE_HISTORY_CACHE_KEY, normalized);
    } catch (err) {
      console.error('Failed to fetch history', err);
      setQuoteHistory(normalizeQuoteHistory(readJson(QUOTE_HISTORY_CACHE_KEY, [])));
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  useEffect(() => {
    writeJson(QUOTE_DRAFT_KEY, {
      client,
      showGstInput,
      items,
      discountPercent,
      gstRate,
      generatedPdfServerUrl,
      generatedPdfServerName,
      quoteNumber,
      quoteDate,
      showBgLogo,
      madeBy,
      madeByPhone,
      madeByEmail,
    });
  }, [
    client,
    showGstInput,
    items,
    discountPercent,
    gstRate,
    generatedPdfServerUrl,
    generatedPdfServerName,
    quoteNumber,
    quoteDate,
    showBgLogo,
    madeBy,
    madeByPhone,
    madeByEmail,
  ]);

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

  useEffect(() => {
    if (cart.length === 0) {
      return;
    }

    setItems((previousItems) => {
      const isBlankDraft =
        previousItems.length === 1 &&
        !previousItems[0].name &&
        !previousItems[0].price &&
        !previousItems[0].rawText;

      return isBlankDraft ? mapCartToItems(cart) : previousItems;
    });
  }, [cart]);

  const requestNotificationPermission = async () => {
    if (typeof window === 'undefined' || !('Notification' in window)) {
      alert('Notifications are not supported on this device/browser.');
      return;
    }

    const permission = await Notification.requestPermission();
    setNotificationPermission(permission);

    if (permission === 'granted') {
      alert('Notifications enabled. You will get an alert when the quotation PDF is generated.');
    }
  };

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
      setItems(data.items && data.items.length > 0 ? data.items : [createBlankItem()]);
      setDiscountPercent(data.discount_percent || 0);
      setGstRate(data.gst_rate || 18);
      setShowGstInput(Boolean(data.gst));
      setGeneratedPdfUrl(null);
      setGeneratedPdfServerUrl('');
      setGeneratedPdfServerName('');
      setQuoteNumber(data.quote_number || '');
      setQuoteDate('');
      setShowBgLogo(Boolean(data.show_bg_logo));
      setMadeBy(data.made_by || '');
      setMadeByPhone(data.made_by_phone || '');
      setMadeByEmail(data.made_by_email || '');
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

  const handleItemValueChange = (index, fieldName, fieldValue) => {
    setItems((previousItems) =>
      previousItems.map((item, itemIndex) =>
        itemIndex === index
          ? { ...item, [fieldName]: fieldValue }
          : item
      )
    );
  };

  const handleItemChange = (index, e) => {
    handleItemValueChange(index, e.target.name, e.target.value);
  };

  const addItem = () => {
    setItems([...items, createBlankItem()]);
  };

  const removeItem = (index) => {
    const newItems = items.filter((_, i) => i !== index);
    setItems(
      newItems.length > 0
        ? newItems
        : [createBlankItem()]
    );
  };

  const startFreshDraft = () => {
    if (!window.confirm('Start a fresh quotation draft?')) {
      return;
    }

    setClient(blankClient);
    setShowGstInput(false);
    setItems(mapCartToItems(cart));
    setDiscountPercent(0);
    setGstRate(18);
    setGeneratedPdfUrl(null);
    setGeneratedPdfServerUrl('');
    setGeneratedPdfServerName('');
    setQuoteNumber('');
    setQuoteDate('');
    setShowBgLogo(false);
    setMadeBy('');
    setMadeByPhone('');
    setMadeByEmail('');
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

  // Group items by their Room/Section field
  const roomGroups = items.reduce((acc, item) => {
    let room = (item.room || '').trim().toUpperCase();
    if (!room) room = "GENERAL"; // Give it a default name if left empty

    if (!acc[room]) acc[room] = 0;

    const gross = getItemTotal(item); // gross after line-item discount

    // Apply global discount
    const globalDiscAmount = gross * (parseFloat(discountPercent || 0) / 100);
    const taxable = gross - globalDiscAmount;

    // Apply GST per-item to get true distributed Grand Total per room
    const itemGstAmount = taxable * (parseFloat(gstRate || 0) / 100);

    acc[room] += (taxable + itemGstAmount);

    return acc;
  }, {});

  // Convert grouped Object to Array with Index for rendering (e.g., 1. KID'S BATHROOM)
  const roomSummaries = Object.keys(roomGroups).map((roomName, idx) => ({
    index: idx + 1,
    name: roomName,
    total: roomGroups[roomName]
  }));

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
    if (isOffline) {
      alert('You are offline. Please reconnect to generate a fresh PDF from the backend.');
      return;
    }

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
        show_bg_logo: showBgLogo,
        made_by: madeBy.trim(),
        made_by_phone: madeByPhone.trim(),
        made_by_email: madeByEmail.trim(),
      };

      const response = await axios.post(`${BASE}/generate-quote`, payload, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      setGeneratedPdfUrl(url);
      const serverPath = response.headers['x-quote-file-url'] || '';
      const serverName = response.headers['x-quote-file-name'] || '';
      const qNum = response.headers['x-quote-number'] || '';
      const serverUrl = serverPath ? resolveAssetUrl(serverPath) : '';
      setGeneratedPdfServerUrl(serverUrl);
      setGeneratedPdfServerName(serverName || '');
      setQuoteNumber(qNum);
      const today = new Date();
      const formattedDate = today.toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' });
      setQuoteDate(formattedDate);
      fetchHistory();
      await notifyQuoteReady(qNum, grandTotal);
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
        showBgLogo ? `🏢 *SHREEJI CERAMICA*` : null,
        showBgLogo ? `Redefining Luxury | Ph: 9033745455` : null,
        showBgLogo ? `═══════════════════════════════════` : null,
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
      const subject = showBgLogo ? `Quotation ${quoteNumber} — Shreeji Ceramica` : `Quotation ${quoteNumber}`;
      const body = [
        `Dear ${client.client_name || 'Customer'},`,
        ``,
        showBgLogo ? `Thank you for your interest in Shreeji Ceramica — Redefining Luxury.` : `Thank you for your interest.`,
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
        showBgLogo ? `For any queries, contact us at:` : null,
        showBgLogo ? `Phone : 9033745455` : null,
        showBgLogo ? `Email : shreejiceramica303@gmail.com` : null,
        showBgLogo ? `Web   : www.shreejiceramica.com` : null,
        ``,
        `Warm regards,`,
        showBgLogo ? `Shreeji Ceramica Team` : `Sales Team`,
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
        <div className="qt-header-row">
          <div>
            <h2>Create New Quotation</h2>
          </div>
          <div className="qt-header-actions">
            <button className="qt-reset-btn" onClick={startFreshDraft}>
              Start Fresh
            </button>
          </div>
        </div>
      </header>

      {(isOffline || generatedPdfServerUrl || notificationPermission === 'granted') && (
        <div className={`qt-status-banner ${isOffline ? 'offline' : 'info'}`}>
          {isOffline && <span>Offline mode active. Draft editing works, but fresh PDF generation needs internet.</span>}
          {!isOffline && generatedPdfServerUrl && <span>Latest PDF link saved. You can reopen and share it later.</span>}
          {notificationPermission === 'granted' && <span>Notifications enabled for PDF-ready alerts.</span>}
        </div>
      )}

      <section className="qt-client-grid" style={{ position: 'relative', zIndex: 9999 }}>
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

        <InlineSearch 
          onAdd={(newItem) => {
            if (!newItem) return;
            setItems((prev) => {
              // Replace the first item if it's completely blank
              const isFirstBlank = prev.length === 1 && !prev[0].name && !prev[0].price && !prev[0].rawText && !prev[0].sku;
              if (isFirstBlank) {
                return [newItem];
              }
              return [...prev, newItem];
            });
            
            // Visual feedback
            const toast = document.createElement('div');
            toast.textContent = `Added: ${newItem.name || 'Product'}`;
            toast.style.cssText = `
              position: fixed; bottom: 30px; right: 30px;
              background: #10b981; color: white; padding: 12px 24px;
              border-radius: 12px; font-weight: 600; z-index: 10002;
              box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
              transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1), transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
              transform: translateY(0);
            `;
            document.body.appendChild(toast);
            setTimeout(() => {
              toast.style.opacity = '0';
              toast.style.transform = 'translateY(20px)';
              setTimeout(() => {
                if (document.body.contains(toast)) document.body.removeChild(toast);
              }, 400);
            }, 2500);
          }} 
        />
      </section>

      <section className="qt-items-section" style={{ position: 'relative', zIndex: 1 }}>
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
                    <img src={resolveAssetUrl(item.image)} alt="thumb" />
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
                <RoomCombobox
                  value={item.room || ''}
                  options={roomOptions}
                  placeholder="Room/Section"
                  onValueChange={(nextValue) => handleItemValueChange(index, 'room', nextValue)}
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
                  name="sku"
                  value={item.sku || ''}
                  placeholder="SKU"
                  onChange={(e) => handleItemChange(index, e)}
                />
                <input
                  className="qt-field"
                  name="size"
                  value={item.size || ''}
                  placeholder="Size"
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
                  readOnly
                />
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* ── PDF Options ────────────────────────────────────────── */}
      {roomSummaries.length > 0 && (
        <div className="qt-room-summary-table-wrap">
          <table className="qt-room-summary-table">
            <thead>
              <tr>
                <th colSpan="2">SUMMARY OF ALL BATH ROOM</th>
              </tr>
            </thead>
            <tbody>
              {roomSummaries.map((smry, idx) => (
                <tr key={idx}>
                  <td>{smry.index}. {smry.name}</td>
                  <td>Rs {smry.total.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                </tr>
              ))}
              <tr className="qt-room-summary-total">
                <td>FINAL AMOUNT</td>
                <td>Rs {roomSummaries.reduce((a, b) => a + b.total, 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      <section className="qt-pdf-options">
        <h4>PDF Options</h4>
        <div className="qt-pdf-opts-row">
          <label className="qt-bg-logo-label">
            <input
              type="checkbox"
              id="bg-logo-checkbox"
              checked={showBgLogo}
              onChange={(e) => setShowBgLogo(e.target.checked)}
              className="qt-bg-logo-check"
            />
            <span className="qt-bg-logo-icon">🏢</span>
            Include Shreeji Office Branding (Letterhead)
          </label>
          <button
            type="button"
            className={`qt-notify-btn ${notificationPermission === 'granted' ? 'enabled' : ''}`}
            onClick={requestNotificationPermission}
          >
            {notificationPermission === 'granted' ? 'Notifications Enabled' : 'Enable Notifications'}
          </button>
        </div>

        <div className="qt-madeby-section">
          <p className="qt-madeby-title">👤 PREPARED BY <span>(Select Staff)</span></p>
          <div className="qt-madeby-fields">
            <div className="qt-madeby-wrap" style={{ gridColumn: 'span 2' }}>
              <select
                className="qt-field qt-madeby-input"
                id="staff-select"
                value={madeBy}
                onChange={handleStaffSelect}
              >
                <option value="">— Select Staff —</option>
                {staffOptions.map(staff => (
                  <option key={staff.name} value={staff.name}>
                    {staff.name} — {staff.phone}
                  </option>
                ))}
              </select>
            </div>
            
            {madeBy && (
              <div className="qt-madeby-wrap">
                <input
                  className="qt-field qt-madeby-input"
                  type="text"
                  placeholder="Staff Phone"
                  value={madeByPhone}
                  readOnly
                  style={{ background: 'rgba(255,255,255,0.05)', opacity: 0.8 }}
                />
              </div>
            )}
          </div>
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
        <div className="qt-history-top">
          <h3 className="qt-history-title">
            Quotation History
            <span className="qt-count-pill">{quoteHistory.length} files</span>
          </h3>
          <div className="qt-history-search">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            <input 
              type="text" 
              placeholder="Find client or quote..." 
              value={historySearchTerm}
              onChange={(e) => setHistorySearchTerm(e.target.value)}
            />
          </div>
        </div>

        {(() => {
          const filtered = quoteHistory.filter(q => 
            q.client.toLowerCase().includes(historySearchTerm.toLowerCase()) ||
            (q.id && q.id.toLowerCase().includes(historySearchTerm.toLowerCase()))
          );

          if (filtered.length === 0) {
            return (
              <div className="qt-history-empty">
                <p>{historySearchTerm ? "No matching records found." : "No quotation records found yet."}</p>
              </div>
            );
          }

          // Grouping logic
          const now = new Date();
          const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
          const yesterday = today - 86400000;

          const groups = { Today: [], Yesterday: [], Older: [] };
          filtered.forEach(q => {
             const ts = q.date * 1000;
             if (ts >= today) groups.Today.push(q);
             else if (ts >= yesterday) groups.Yesterday.push(q);
             else groups.Older.push(q);
          });

          return Object.entries(groups).map(([label, records]) => {
            if (records.length === 0) return null;
            return (
              <div key={label} className="qt-history-group">
                <h4 className="qt-group-label">{label}</h4>
                <div className="qt-records-list">
                  {records.map(q => {
                    const initials = (q.client || 'C').charAt(0).toUpperCase();
                    return (
                      <article key={q.id} className="qt-record-list-item">
                        <div className="qt-record-avatar" style={{ '--bg': `hsl(${(initials.charCodeAt(0) * 10) % 360}, 65%, 45%)` }}>
                          {initials}
                        </div>
                        <div className="qt-record-main">
                          <div className="qt-record-info">
                            <span className="qt-record-name">{q.client}</span>
                            <span className="qt-record-date">
                              📅 {new Date(q.date * 1000).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })} • 
                              {new Date(q.date * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          <div className="qt-record-amount">
                            ₹{q.total.toLocaleString('en-IN')}
                          </div>
                        </div>
                        <div className="qt-record-row-actions">
                          <button onClick={() => loadQuote(q.id)} className="qt-action-icon edit" title="Resume Edit">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
                          </button>
                          <button onClick={() => deleteQuote(q.id)} className="qt-action-icon delete" title="Delete">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </div>
            );
          });
        })()}
      </section>
    </div>
  );
}
