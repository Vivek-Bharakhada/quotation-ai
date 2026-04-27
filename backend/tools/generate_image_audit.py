import json
import os
import sys

# Setup paths relative to backend
# Assuming script is in backend/tools/
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_FILE = os.path.join(BACKEND_DIR, "search_index_v2.json")
OUTPUT_FILE = os.path.join(BACKEND_DIR, "image_audit_report.html")

def resolve_local_path(img_static_path):
    if not img_static_path:
        return None
    # /static/images/Aquant/123.png -> static/images/Aquant/123.png
    rel = img_static_path.lstrip("/")
    # Check if the file exists in the backend directory
    full_path = os.path.join(BACKEND_DIR, rel)
    return full_path if os.path.exists(full_path) else None

def generate_report():
    if not os.path.exists(INDEX_FILE):
        print(f"Error: {INDEX_FILE} not found.")
        return

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        items = data.get("stored_items", [])

    print(f"Loaded {len(items)} items. Auditing images...")

    report_items = []
    missing_count = 0
    ok_count = 0

    for item in items:
        name = item.get("name", "N/A")
        code = item.get("search_code") or item.get("base_code") or "N/A"
        brand = item.get("brand", "Unknown")
        images = item.get("images", [])
        
        img_path = images[0] if images else None
        local_path = resolve_local_path(img_path)
        
        status = "OK" if local_path else "MISSING"
        if status == "MISSING":
            missing_count += 1
        else:
            ok_count += 1

        report_items.append({
            "name": name,
            "code": code,
            "brand": brand,
            "image_url": img_path,
            "status": status,
            "price": item.get("price", "0")
        })

    # Generate HTML
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Product Image Audit Report</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
            .container { max-width: 1400px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            .stats { display: flex; gap: 20px; margin-bottom: 20px; }
            .stat-card { padding: 15px 25px; border-radius: 8px; color: white; flex: 1; text-align: center; font-weight: bold; }
            .stat-total { background: #34495e; }
            .stat-ok { background: #27ae60; }
            .stat-missing { background: #e74c3c; }
            
            .filters { margin-bottom: 20px; display: flex; gap: 10px; align-items: center; background: #ecf0f1; padding: 15px; border-radius: 8px; }
            input[type="text"] { padding: 10px; border: 1px solid #bdc3c7; border-radius: 4px; flex: 1; }
            select { padding: 10px; border: 1px solid #bdc3c7; border-radius: 4px; }
            
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th { background: #3498db; color: white; padding: 12px; text-align: left; position: sticky; top: 0; }
            td { padding: 12px; border-bottom: 1px solid #eee; vertical-align: middle; }
            tr:hover { background: #f9f9f9; }
            
            .img-container { width: 100px; height: 100px; border: 1px solid #ddd; border-radius: 4px; overflow: hidden; background: #eee; display: flex; align-items: center; justify-content: center; }
            img { max-width: 100%; max-height: 100%; object-fit: contain; }
            
            .status-tag { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; text-transform: uppercase; }
            .status-ok { background: #d4edda; color: #155724; }
            .status-missing { background: #f8d7da; color: #721c24; }
            
            .brand-tag { background: #e1f5fe; color: #01579b; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
            
            .hidden { display: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Product Image Audit Report</h1>
            
            <div class="stats">
                <div class="stat-card stat-total">Total Items: <span id="total-val">0</span></div>
                <div class="stat-card stat-ok">Images OK: <span id="ok-val">0</span></div>
                <div class="stat-card stat-missing">Missing Images: <span id="missing-val">0</span></div>
            </div>

            <div class="filters">
                <input type="text" id="searchInput" placeholder="Search by name or code..." onkeyup="filterTable()">
                <select id="brandFilter" onchange="filterTable()">
                    <option value="">All Brands</option>
                    <option value="Aquant">Aquant</option>
                    <option value="Kohler">Kohler</option>
                </select>
                <select id="statusFilter" onchange="filterTable()">
                    <option value="">All Status</option>
                    <option value="OK">OK</option>
                    <option value="MISSING">Missing Only</option>
                </select>
                <button onclick="window.location.reload()" style="padding: 10px 15px; cursor: pointer; background: #3498db; color: white; border: none; border-radius: 4px;">Refresh</button>
            </div>

            <table id="auditTable">
                <thead>
                    <tr>
                        <th>Image</th>
                        <th>Product Details</th>
                        <th>Brand</th>
                        <th>Status</th>
                        <th>Path</th>
                    </tr>
                </thead>
                <tbody>
                    {% ROWS %}
                </tbody>
            </table>
        </div>

        <script>
            function filterTable() {
                const search = document.getElementById('searchInput').value.toLowerCase();
                const brand = document.getElementById('brandFilter').value;
                const status = document.getElementById('statusFilter').value;
                const rows = document.getElementById('auditTable').getElementsByTagName('tbody')[0].getElementsByTagName('tr');

                let visibleCount = 0;

                for (let i = 0; i < rows.length; i++) {
                    const row = rows[i];
                    const name = row.getAttribute('data-name').toLowerCase();
                    const code = row.getAttribute('data-code').toLowerCase();
                    const rBrand = row.getAttribute('data-brand');
                    const rStatus = row.getAttribute('data-status');

                    const matchesSearch = name.includes(search) || code.includes(search);
                    const matchesBrand = brand === "" || rBrand === brand;
                    const matchesStatus = status === "" || (status === "MISSING" && rStatus === "MISSING") || (status === "OK" && rStatus === "OK");

                    if (matchesSearch && matchesBrand && matchesStatus) {
                        row.classList.remove('hidden');
                        visibleCount++;
                    } else {
                        row.classList.add('hidden');
                    }
                }
            }
            
            // Set initial stats
            document.getElementById('total-val').innerText = "%TOTAL%";
            document.getElementById('ok-val').innerText = "%OK%";
            document.getElementById('missing-val').innerText = "%MISSING%";
        </script>
    </body>
    </html>
    """

    rows_html = []
    for item in report_items:
        status_cls = "status-ok" if item["status"] == "OK" else "status-missing"
        # In the HTML file sitting in 'backend/', the images are at 'static/images/...'
        img_src = item["image_url"].lstrip("/") if item["image_url"] else ""
        img_tag = f'<img src="{img_src}" alt="No Image">' if img_src else '<span>No URL</span>'
        
        row = f"""
        <tr data-name="{item['name']}" data-code="{item['code']}" data-brand="{item['brand']}" data-status="{item['status']}">
            <td><div class="img-container">{img_tag}</div></td>
            <td>
                <strong>{item['name']}</strong><br>
                <small style="color: #666">Code: {item['code']}</small><br>
                <small>Price: ₹{item['price']}</small>
            </td>
            <td><span class="brand-tag">{item['brand']}</span></td>
            <td><span class="status-tag {status_cls}">{item['status']}</span></td>
            <td style="font-size: 11px; color: #888; max-width: 200px; word-break: break-all;">{item['image_url'] or 'N/A'}</td>
        </tr>
        """
        rows_html.append(row)

    final_html = html_template.replace("{% ROWS %}", "\n".join(rows_html))
    final_html = final_html.replace("%TOTAL%", str(len(items)))
    final_html = final_html.replace("%OK%", str(ok_count))
    final_html = final_html.replace("%MISSING%", str(missing_count))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Report generated: {OUTPUT_FILE}")
    print(f"Total: {len(items)}, OK: {ok_count}, Missing: {missing_count}")

if __name__ == "__main__":
    generate_report()
