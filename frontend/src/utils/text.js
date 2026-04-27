export function sanitizeDisplayText(value) {
  const raw = String(value ?? '');
  if (!raw) {
    return '';
  }

  let text = raw;
  if (/[ÃâÂ]/.test(text)) {
    try {
      text = decodeURIComponent(escape(text));
    } catch {
      text = raw;
    }
  }

  return text
    .normalize('NFKC')
    .replace(/\u00a0/g, ' ')
    .replace(/₹/g, 'Rs ')
    .replace(/™/g, ' TM ')
    .replace(/[‘’]/g, "'")
    .replace(/[“”]/g, '"')
    .replace(/[–—]/g, '-')
    .replace(/[•●]/g, '-')
    .replace(/â€™/g, "'")
    .replace(/â€œ|â€/g, '"')
    .replace(/â€“|â€”/g, '-')
    .replace(/â€¢/g, '-')
    .replace(/â„¢/g, ' TM ')
    .replace(/â‚¹/g, 'Rs ')
    .replace(/Ã‚/g, '')
    .replace(/Â/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim();
}
