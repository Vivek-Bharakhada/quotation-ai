# Cross Platform Setup

This project now includes a production-oriented foundation for:

- `Web + PWA`
- `Android / iPhone shell via Capacitor`
- `Desktop shell via Electron`

## What was added

- Installable PWA manifest and service worker
- Local draft persistence for cart, page, theme, search state, and quotation form
- Offline-friendly banners and cached search fallback
- Backend URL override screen inside the app
- `frontend/capacitor.config.json` for mobile packaging
- `frontend/electron/main.js` and `frontend/electron/preload.js` for desktop packaging

## Backend requirement

For mobile and desktop builds, point the frontend to a deployed FastAPI backend.

Inside the app:

1. Open `Settings`
2. Enter your deployed backend URL
3. Save and reload

Example:

```text
https://your-backend-domain.com
```

## PWA

From the `frontend` folder:

```bash
npm install
npm run build
```

Deploy the `frontend/build` output as usual.

When opened in Chrome, Edge, or supported mobile browsers, the app can be installed with:

- `Install App`
- `Add to Home Screen`

## Desktop app

From the `frontend` folder:

```bash
npm install
npm run build:app
npm run desktop:start
```

For development against the React dev server:

```bash
npm start
npm run desktop:dev
```

## Android / iPhone app

From the `frontend` folder:

```bash
npm install
npm run build:app
npm run mobile:sync
```

Then add platforms once on a machine with the right SDKs:

```bash
npx cap add android
npx cap add ios
```

Open the native projects:

```bash
npm run mobile:open:android
npm run mobile:open:ios
```

## Important publishing notes

- `iPhone builds require macOS + Xcode`
- `Android builds require Android Studio`
- File upload, PDF download, WhatsApp share, and email flows must be tested on real devices
- Push notifications are not fully native yet; the current implementation enables browser/PWA notifications for PDF-ready alerts
- The backend must be online for live search, uploads, and fresh PDF generation

## Recommended next release tasks

- Add real auth on the backend before public rollout
- Add native share / file plugins in Capacitor if you want a smoother mobile experience
- Add desktop packaging and installer tooling if you want `.exe` distribution
- Run a full device QA pass on Android, iPhone, Windows laptop, and iPad
