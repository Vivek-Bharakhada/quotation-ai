import BASE from '../api';

const ABSOLUTE_PROTOCOL = /^(https?:|data:|blob:)/i;

export function isAbsoluteUrl(value) {
  return ABSOLUTE_PROTOCOL.test(String(value || '').trim());
}

export function resolveAssetUrl(value) {
  const raw = String(value || '').trim();
  if (!raw) {
    return '';
  }
  if (isAbsoluteUrl(raw)) {
    return raw;
  }
  if (raw.startsWith('//')) {
    return `https:${raw}`;
  }

  const normalizedBase = String(BASE || '').trim().replace(/\/+$/, '');
  if (!normalizedBase) {
    return raw;
  }

  if (raw.startsWith('/')) {
    return `${normalizedBase}${raw}`;
  }

  return `${normalizedBase}/${raw}`;
}
