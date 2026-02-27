print("--- BACKEND STARTING ---")
print("Importing FastAPI...")
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
print("Importing shutil/os...")
import shutil
import os
import json
import time
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlparse
import httpx
print("Importing custom modules...")
from pdf_reader import extract_content, chunk_content
import search_engine
from quotation import generate_quote
print("Done with imports!")

from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount static folder for images
os.makedirs(os.path.join("static", "images"), exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Quote-File-Url", "X-Quote-File-Name", "X-Quote-Number"],
)

import threading

def index_local_catalogs(force=False):
    # Helper to prevent multiple simultaneous indexes
    if getattr(index_local_catalogs, "_running", False):
        return
    index_local_catalogs._running = True
    
    import search_engine
    if not force and len(search_engine.stored_items) > 0:
        print("--- INDEX ALREADY LOADED, SKIPPING BACKGROUND SCAN ---")
        index_local_catalogs._running = False
        return

    print("--- BACKGROUND INDEXING START ---")
    search_engine.reset_index()  # Clean all stored data and AI vectors

    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        index_local_catalogs._running = False
        return

    files = [f for f in os.listdir(upload_dir) if f.lower().endswith(".pdf")]
    for filename in files:
        if "aquant" in filename.lower():
            brand = "Aquant"
        elif "kohler" in filename.lower():
            brand = "Kohler"
        else:
            continue
        
        path = os.path.join(upload_dir, filename)
        try:
            items = extract_content(path)
            search_engine.add_to_index(None, items)
            print(f"Indexed: {filename} as {brand}")
        except Exception as e:
            print(f"Error indexing {filename}: {e}")
    
    print(f"--- BACKGROUND INDEXING COMPLETE ---")
    search_engine.load_index()
    index_local_catalogs._running = False

def _bool_env(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, str(default))).strip().lower()
    return raw in {"1", "true", "yes", "on"}

def _normalize_whatsapp_number(raw_number: str) -> str:
    digits = "".join(ch for ch in str(raw_number or "") if ch.isdigit())
    if len(digits) == 10:
        return f"91{digits}"
    if len(digits) == 11 and digits.startswith("0"):
        return f"91{digits[1:]}"
    if len(digits) >= 12 and digits.startswith("91"):
        return digits
    return digits

def _resolve_static_pdf_path(pdf_url: str):
    if not pdf_url:
        raise HTTPException(status_code=400, detail="Missing pdf_url")

    parsed = urlparse(pdf_url)
    raw_path = parsed.path if parsed.scheme else str(pdf_url)
    if not raw_path.startswith("/static/"):
        raise HTTPException(status_code=400, detail="pdf_url must point to /static/*")

    rel_path = raw_path.lstrip("/")
    static_root = os.path.abspath("static")
    abs_path = os.path.abspath(os.path.normpath(rel_path))

    # Prevent path traversal outside static folder.
    if not abs_path.startswith(static_root):
        raise HTTPException(status_code=400, detail="Invalid pdf_url path")

    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="PDF file not found on server")

    return abs_path, os.path.basename(abs_path), raw_path

@app.on_event("startup")
async def startup_event():
    import search_engine
    # Try to load existing index first
    if not search_engine.load_index():
        # Only index if no saved index found
        threading.Thread(target=index_local_catalogs, daemon=True).start()
    else:
        print("Using saved search index.")


@app.get("/refresh")
async def refresh_catalogs():
    threading.Thread(target=index_local_catalogs, args=(True,), daemon=True).start()
    return {"message": "Indexing started in background. Results will appear shortly."}

@app.get("/status")
def get_status():
    import search_engine
    total = len(search_engine.stored_items)
    samples = []
    for item in search_engine.stored_items[:5]:
        samples.append({
            "text": item["text"][:100], 
            "page": item["page"],
            "source": item.get("source", "N/A")
        })
    return {
        "indexed_items": total,
        "faiss_ready": search_engine.vector_index is not None,
        "sample_items": samples
    }




@app.post("/generate-quote")
async def create_quote(data: dict):
    # Save quotation data for history.
    os.makedirs("quotes_history", exist_ok=True)
    timestamp = int(time.time())
    client_slug = data.get("client_name", "Unknown").replace(" ", "_")

    # Auto-generate a readable quotation number: SC-YYYYMMDD-XXXX
    from datetime import datetime
    date_str = datetime.now().strftime("%Y%m%d")
    seq = str(timestamp)[-4:]          # last 4 digits of unix timestamp
    quote_number = f"SC-{date_str}-{seq}"
    data["quote_number"] = quote_number

    filename = f"quote_{timestamp}_{client_slug}.json"
    with open(os.path.join("quotes_history", filename), "w") as f:
        json.dump(data, f)

    generate_quote(data)

    # Keep a shareable static copy of the generated PDF for email/WhatsApp sending.
    os.makedirs(os.path.join("static", "quotes"), exist_ok=True)
    share_pdf_name = f"quote_{timestamp}_{client_slug}.pdf"
    share_pdf_path = os.path.join("static", "quotes", share_pdf_name)
    shutil.copyfile("quotation.pdf", share_pdf_path)
    share_pdf_url = f"/static/quotes/{share_pdf_name}"

    return FileResponse(
        "quotation.pdf",
        media_type="application/pdf",
        filename="quotation.pdf",
        headers={
            "X-Quote-File-Url":    share_pdf_url,
            "X-Quote-File-Name":   share_pdf_name,
            "X-Quote-Number":      quote_number,
        },
    )

@app.post("/send-quote-email")
async def send_quote_email(data: dict):
    to_email = str(data.get("to_email") or "").strip()
    subject = str(data.get("subject") or "Quotation PDF").strip()
    body = str(data.get("body") or "").strip()
    pdf_url = str(data.get("pdf_url") or "").strip()
    requested_name = str(data.get("pdf_filename") or "").strip()

    if not to_email:
        raise HTTPException(status_code=400, detail="Recipient email is required")

    pdf_path, detected_name, _ = _resolve_static_pdf_path(pdf_url)
    pdf_name = requested_name or detected_name

    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").strip()
    smtp_from = os.getenv("SMTP_FROM", smtp_user).strip()
    smtp_ssl = _bool_env("SMTP_SSL", False)
    smtp_starttls = _bool_env("SMTP_STARTTLS", True)

    if not smtp_host:
        raise HTTPException(status_code=500, detail="SMTP not configured: missing SMTP_HOST")
    if not smtp_from:
        raise HTTPException(status_code=500, detail="SMTP not configured: missing SMTP_FROM/SMTP_USER")

    try:
        msg = EmailMessage()
        msg["From"] = smtp_from
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body or "Please find your quotation attached.")

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=pdf_name)

        if smtp_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=ssl.create_default_context(), timeout=30) as server:
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.ehlo()
                if smtp_starttls:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email send failed: {e}")

    return {"message": "Email sent with PDF attachment"}

@app.post("/send-quote-whatsapp")
async def send_quote_whatsapp(data: dict):
    raw_to = str(data.get("to_number") or "").strip()
    body = str(data.get("body") or "").strip()
    pdf_url = str(data.get("pdf_url") or "").strip()
    requested_name = str(data.get("pdf_filename") or "").strip()

    to_number = _normalize_whatsapp_number(raw_to)
    if not to_number:
        raise HTTPException(status_code=400, detail="Valid WhatsApp number is required")

    token = os.getenv("WHATSAPP_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    if not token or not phone_number_id:
        raise HTTPException(
            status_code=500,
            detail="WhatsApp API not configured: set WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID",
        )

    pdf_path, detected_name, _ = _resolve_static_pdf_path(pdf_url)
    pdf_name = requested_name or detected_name

    base_url = f"https://graph.facebook.com/v20.0/{phone_number_id}"
    auth_headers = {"Authorization": f"Bearer {token}"}

    try:
        # Send detailed text first.
        if body:
            text_payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {"body": body[:4000]},
            }
            text_res = httpx.post(
                f"{base_url}/messages",
                headers={**auth_headers, "Content-Type": "application/json"},
                json=text_payload,
                timeout=45,
            )
            if not text_res.is_success:
                raise HTTPException(status_code=500, detail=f"WhatsApp text send failed: {text_res.text}")

        # Upload document media.
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_name, f, "application/pdf")}
            media_payload = {"messaging_product": "whatsapp", "type": "application/pdf"}
            media_res = httpx.post(
                f"{base_url}/media",
                headers=auth_headers,
                data=media_payload,
                files=files,
                timeout=60,
            )
        if not media_res.is_success:
            raise HTTPException(status_code=500, detail=f"WhatsApp media upload failed: {media_res.text}")

        media_id = (media_res.json() or {}).get("id")
        if not media_id:
            raise HTTPException(status_code=500, detail="WhatsApp media upload failed: no media id returned")

        # Send uploaded PDF as document.
        doc_payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "document",
            "document": {
                "id": media_id,
                "filename": pdf_name,
                "caption": "Quotation PDF attached.",
            },
        }
        doc_res = httpx.post(
            f"{base_url}/messages",
            headers={**auth_headers, "Content-Type": "application/json"},
            json=doc_payload,
            timeout=45,
        )
        if not doc_res.is_success:
            raise HTTPException(status_code=500, detail=f"WhatsApp document send failed: {doc_res.text}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WhatsApp send failed: {e}")

    return {"message": "WhatsApp sent with PDF document"}

@app.get("/list-quotes")
def list_quotes():
    folder = "quotes_history"
    if not os.path.exists(folder):
        return {"quotes": []}
    files = [f for f in os.listdir(folder) if f.endswith(".json")]
    details = []
    for f in files:
        path = os.path.join(folder, f)
        stat = os.stat(path)
        with open(path, "r") as jf:
            try:
                content = json.load(jf)
                details.append({
                    "id": f,
                    "client": content.get("client_name", "N/A"),
                    "total": content.get("grand_total", 0),
                    "date": stat.st_mtime
                })
            except: continue
    details.sort(key=lambda x: x["date"], reverse=True)
    return {"quotes": details}

@app.get("/get-quote/{id}")
def get_quote(id: str):
    path = os.path.join("quotes_history", id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    raise HTTPException(status_code=404)

@app.delete("/delete-quote/{id}")
def delete_quote(id: str):
    path = os.path.join("quotes_history", id)
    if os.path.exists(path):
        os.remove(path)
        return {"message": "Deleted"}
    raise HTTPException(status_code=404)



@app.get("/search")
def search_item(q: str, brand: str = None, smart: bool = False, exact: bool = False):
    # Handle "all" brand from frontend if it slips through
    if brand == "all": brand = None
    
    print(f"DEBUG: Search request: q='{q}', brand='{brand}', smart={smart}, exact={exact}")
    results = search_engine.search(q, smart=smart, brand=brand)
    if exact:
        results = results[:1]
    print(f"DEBUG: Found {len(results)} results")
    return {"results": results}

@app.post("/catalog/add")
async def add_manual_item(
    name: str = Form(...),
    price: str = Form(...),
    brand: str = Form(...),
    category: str = Form(""),
    file: UploadFile = File(None)
):
    import search_engine
    
    image_path = None
    if file:
        dest_dir = os.path.join("static", "images", "manual")
        os.makedirs(dest_dir, exist_ok=True)
        img_filename = f"manual_{int(time.time())}_{file.filename}"
        dest_path = os.path.join(dest_dir, img_filename)
        
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        image_path = f"/static/images/manual/{img_filename}"
        
    new_item = {
        "text": f"{name}\nMRP : ` {price}/-",
        "name": name,
        "price": price,
        "page": 0,
        "source": "Manual Entry",
        "images": [image_path] if image_path else [],
        "brand": brand,
        "category": category
    }
    
    search_engine.add_to_index(None, [new_item])
    search_engine.save_index()
    
    return {"message": "Success", "item": new_item}
@app.get("/ask")
def ask_question(q: str):
    # SMART mode for deep analysis
    results = search_engine.search(q, smart=True)
    if not results:
        return {"answer": "No results found in the catalog for your query."}
    
    # Just return a summary of the top result so it doesn't flood the UI with details
    top_result_text = results[0]["text"].replace("\n", " ").strip()
    if len(top_result_text) > 150:
        top_result_text = top_result_text[:150] + "..."
        
    answer = f"Top match from catalog:\n• {top_result_text}\n(See exact match details in the cards below)"
    return {"answer": answer}



@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        os.makedirs("uploads", exist_ok=True)
        path = os.path.join("uploads", file.filename)
        content = await file.read()
        with open(path, "wb") as buffer:
            buffer.write(content)
        # Run indexing in background — don't block the response
        threading.Thread(target=index_local_catalogs, args=(True,), daemon=True).start()
        return {"message": f"'{file.filename}' uploaded! Indexing in background..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list-uploads")
def list_uploads():
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        return {"files": []}
    files = [f for f in os.listdir(upload_dir) if f.lower().endswith(".pdf")]
    # Get file stats (size and date)
    file_details = []
    for f in files:
        path = os.path.join(upload_dir, f)
        stat = os.stat(path)
        file_details.append({
            "name": f,
            "size": round(stat.st_size / (1024 * 1024), 2), # MB
            "date": stat.st_mtime
        })
    # Sort by date descending
    file_details.sort(key=lambda x: x["date"], reverse=True)
    return {"files": file_details}

@app.delete("/delete-upload/{filename}")
def delete_upload(filename: str):
    path = os.path.join("uploads", filename)
    if os.path.exists(path):
        os.remove(path)
        # Re-index in background after deletion
        threading.Thread(target=index_local_catalogs, args=(True,), daemon=True).start()
        return {"message": f"'{filename}' deleted and system re-indexed."}
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/rename-upload")
def rename_upload(data: dict):
    old_name = data.get("old_name")
    new_name = data.get("new_name")
    
    if not old_name or not new_name:
        raise HTTPException(status_code=400, detail="Missing names")
        
    old_path = os.path.join("uploads", old_name)
    new_path = os.path.join("uploads", new_name)
    
    if not os.path.exists(old_path):
        raise HTTPException(status_code=404, detail="Original file not found")
        
    if os.path.exists(new_path):
        raise HTTPException(status_code=400, detail="New filename already exists")
        
    os.rename(old_path, new_path)
    # Re-index in background after rename
    threading.Thread(target=index_local_catalogs, args=(True,), daemon=True).start()
    return {"message": f"Renamed to {new_name}"}

@app.get("/catalog/index")
def get_catalog_index():
    import search_engine
    import re
    
    # Check cache first for instant loading
    if search_engine.catalog_summary_cache:
        return search_engine.catalog_summary_cache
        
    if not search_engine.stored_items:
        search_engine.load_index()
    
    if not search_engine.stored_items:
        return []
        
    brand_map = {}
    # Iterate through all items just once and build the summary
    for item in search_engine.stored_items:
        brand = item.get("brand")
        if not brand:
            src = str(item.get("source") or "Generic").lower()
            brand = "Kohler" if "kohler" in src else "Aquant" if "aquant" in src else "Generic"
        
        if brand not in brand_map:
            brand_map[brand] = {"name": brand, "collections": set()}
            
        # Use the 'category' field if available
        h = item.get("category")
        if h:
            brand_map[brand]["collections"].add(h)
        else:
            # Fallback for older indexed items or undetected headers
            if "text" in item:
                first_line = item["text"].split("\n")[0].strip()
            heading_match = re.match(r'^([A-Z\s]{4,28})', first_line)
            if heading_match:
                h = heading_match.group(1).strip()
                if len(h) > 3:
                    brand_map[brand]["collections"].add(h)

    result = []
    # Always prioritize the big two for display
    for b_name in ["Aquant", "Kohler"]:
        if b_name in brand_map:
            b_data = brand_map.pop(b_name)
            cols = sorted(list(b_data["collections"])) or ["Standard Products"]
            result.append({"brand": b_name, "collections": cols[:25]})

    # Add any remaining brands
    for brand_name, b_data in sorted(brand_map.items()):
        cols = sorted(list(b_data["collections"])) or ["Standard Products"]
        result.append({"brand": brand_name, "collections": cols[:25]})

    # Save to cache
    search_engine.catalog_summary_cache = result
    return result

@app.get("/catalog/browse")
def browse_collection(brand: str, collection: str = None):
    import search_engine
    results = []
    brand_lower = brand.lower()
    collection_lower = (collection or "").lower()
    
    for item in search_engine.stored_items:
        # Strict brand check using the new indexed 'brand' field
        item_brand = item.get("brand", "").lower() or item.get("source", "").lower()
        if brand_lower not in item_brand:
            continue
            
        # Collection / Category check
        if not collection or collection == "All Products" or collection == "Standard Products":
            results.append(item)
        else:
            item_cat = str(item.get("category", "")).lower()
            item_text = item.get("text", "").lower()

            # Kohler dashboard has fixed sections; use semantic fallbacks for empty categories.
            if brand_lower == "kohler" and collection_lower == "toilets":
                toilet_cats = {
                    "toilets",
                    "smart toilets & bidet seats",
                    "1 pc toilets & wall hungs",
                    "in-wall tanks",
                }
                if item_cat in toilet_cats or any(k in item_text for k in ["toilet", "bidet", "cleansing seat"]):
                    results.append(item)
            elif brand_lower == "kohler" and collection_lower == "in-wall tanks":
                if ("wall" in item_cat and "tank" in item_cat) or any(
                    k in item_text for k in ["in-wall", "concealed tank", "concealed cistern", "dual flush tank", "tank only"]
                ):
                    results.append(item)
            elif brand_lower == "kohler" and collection_lower == "cleaning solutions":
                if item_cat == "cleaning solutions" or any(k in item_text for k in ["cleaner", "cleaning solution", "descaler"]):
                    results.append(item)
            elif collection_lower in item_cat:
                results.append(item)
            elif collection_lower in item_text:
                # Fallback to text matching for broader reach
                results.append(item)
            
        if len(results) >= 500: break # Show more for browsing
    
    return {"results": results}
