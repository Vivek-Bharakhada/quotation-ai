const isBrowser = typeof window !== 'undefined';

export function readJson(key, fallback) {
  if (!isBrowser) {
    return fallback;
  }

  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      return fallback;
    }
    return JSON.parse(raw);
  } catch (error) {
    console.warn(`Unable to read localStorage key "${key}"`, error);
    return fallback;
  }
}

export function writeJson(key, value) {
  if (!isBrowser) {
    return;
  }

  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.warn(`Unable to write localStorage key "${key}"`, error);
  }
}

export function readString(key, fallback = '') {
  if (!isBrowser) {
    return fallback;
  }

  try {
    const value = window.localStorage.getItem(key);
    return value ?? fallback;
  } catch (error) {
    console.warn(`Unable to read localStorage key "${key}"`, error);
    return fallback;
  }
}

export function writeString(key, value) {
  if (!isBrowser) {
    return;
  }

  try {
    window.localStorage.setItem(key, value);
  } catch (error) {
    console.warn(`Unable to write localStorage key "${key}"`, error);
  }
}

export function removeValue(key) {
  if (!isBrowser) {
    return;
  }

  try {
    window.localStorage.removeItem(key);
  } catch (error) {
    console.warn(`Unable to remove localStorage key "${key}"`, error);
  }
}
