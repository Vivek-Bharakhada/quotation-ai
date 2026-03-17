# Production Setup

This project now supports a cloud-backed deployment path that keeps the current FastAPI + React architecture and adds optional Supabase storage plus Resend email delivery.

## Backend environment

Create the variables from `backend/.env.example`.

Minimum production set:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`
- `WHATSAPP_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`

## Supabase buckets

Create these public buckets:

- `catalogs`
- `quote-history`
- `quotes`
- `product-images`
- `system`

## What is now cloud-aware

- Uploaded catalog PDFs
- Generated quotation PDFs
- Manual and extracted product images
- Quote history JSON files
- Search index JSON snapshot

## Frontend environment

Create the variable from `frontend/.env.example`.

- `REACT_APP_API_URL=https://api.yourdomain.com`

## Deployment order

1. Create Supabase project and buckets.
2. Add backend env vars on Railway.
3. Deploy FastAPI backend.
4. Add `REACT_APP_API_URL` on Vercel.
5. Deploy frontend.
6. Re-upload or refresh catalogs once so fresh image URLs are written into the search index.

## Notes

- Existing local mode still works when Supabase variables are missing.
- Frontend now supports both relative `/static/...` paths and full cloud URLs.
- Search still uses the current in-memory/index JSON engine; cloud sync is used to persist that index between deploys.
