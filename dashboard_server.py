from flask import Flask, render_template_string, jsonify, send_from_directory, request
import json
import os
import subprocess
import time

app = Flask(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets/images")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

PROJECTS = {
    "nulledscripts": {
        "results": os.path.join(DATA_DIR, "results.json"),
        "queue": os.path.join(DATA_DIR, "queue.json"),
        "color": "#00f2ff"
    },
    "nullphpscript": {
        "results": os.path.join(DATA_DIR, "results_nullphp.json"),
        "queue": os.path.join(DATA_DIR, "queue_nullphp.json"),
        "color": "#f1c40f"
    }
}

@app.route('/assets/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(ASSETS_DIR, filename)

def get_stats(project_id):
    p = PROJECTS.get(project_id)
    if not p: return {}
    
    try:
        with open(p["queue"], "r") as f:
            total = len(json.load(f))
    except: total = 0
        
    try:
        if not os.path.exists(p["results"]):
            with open(p["results"], "w") as f: json.dump([], f)
            
        with open(p["results"], "r") as f:
            results = json.load(f)
            done = len(results)
            # Only send the last 20 items to keep it light
            raw_last = results[-20:] if results else []
            
            # Truncate description for the list view to save MBs of data
            last_items = []
            for item in raw_last:
                item_copy = item.copy()
                if len(item_copy.get('description_html', '')) > 200:
                    item_copy['description_html'] = item_copy['description_html'][:200] + "..."
                last_items.append(item_copy)
                
            failures = sum(1 for item in results if "Checking your browser" in item.get("title", "") or not item.get("title"))
            active_links = sum(1 for item in results if item.get("link_status") == "Active")
    except:
        done = 0
        last_items = []
        failures = 0
        active_links = 0
        
    return {
        "total": total,
        "done": done,
        "failures": failures,
        "active_links": active_links,
        "progress": round((done / total * 100), 1) if total > 0 else 0,
        "last_items": last_items,
        "status": "Ready"
    }

@app.route("/api/stats")
def api_all_stats():
    return jsonify({pid: get_stats(pid) for pid in PROJECTS})

@app.route("/api/details/<project_id>/<item_id>")
def get_item_details(project_id, item_id):
    p = PROJECTS.get(project_id)
    if not p: return jsonify({"error": "Project not found"})
    try:
        with open(p["results"], "r") as f:
            results = json.load(f)
            item = next((i for i in results if i['id'] == item_id), None)
            return jsonify(item)
    except:
        return jsonify({"error": "Item not found"})

@app.route("/api/push/github", methods=["POST"])
def push_github():
    try:
        subprocess.run(["git", "add", "."], cwd=BASE_DIR)
        subprocess.run(["git", "commit", "-m", "Portfolio Update"], cwd=BASE_DIR)
        return jsonify({"status": "success", "message": "Changes committed locally. Push to remote ready."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Goox Command Center Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #050508; --card: rgba(255, 255, 255, 0.02); --accent: #00f2ff; --accent2: #f1c40f; --text: #fff; }
        body { background: var(--bg); color: var(--text); font-family: 'Outfit'; margin: 0; min-height: 100vh; }
        .navbar { display: flex; justify-content: space-between; padding: 20px 40px; background: rgba(0,0,0,0.5); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255,255,255,0.05); }
        .project-tabs { display: flex; gap: 10px; padding: 30px 40px 10px 40px; }
        .tab { padding: 12px 25px; border-radius: 12px; background: var(--card); border: 1px solid rgba(255,255,255,0.05); cursor: pointer; color: #555; transition: 0.3s; }
        .tab.active { background: rgba(255,255,255,0.05); border-color: var(--accent); color: #fff; }
        .main { padding: 0 40px 40px 40px; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: var(--card); border: 1px solid rgba(255,255,255,0.05); padding: 25px; border-radius: 20px; }
        .label { font-size: 10px; text-transform: uppercase; color: #666; letter-spacing: 1px; }
        .value { font-size: 32px; font-weight: 700; margin-top: 5px; }
        .feed-wrap { background: var(--card); border-radius: 25px; padding: 25px; border: 1px solid rgba(255,255,255,0.05); max-height: 700px; overflow-y: auto; }
        .item-row { display: grid; grid-template-columns: 70px 1fr 150px 120px 120px; align-items: center; padding: 15px; background: rgba(255,255,255,0.01); border-radius: 15px; margin-bottom: 10px; transition: 0.2s; }
        .item-row:hover { background: rgba(255,255,255,0.03); }
        .thumb { width: 50px; height: 50px; border-radius: 10px; object-fit: cover; background: #111; }
        .title { font-weight: 600; font-size: 15px; }
        .meta { font-size: 11px; color: #444; }
        .badge { font-size: 10px; padding: 4px 10px; border-radius: 6px; text-transform: uppercase; font-weight: 700; }
        .btn-detail { background: rgba(255,255,255,0.05); color: #fff; border: 1px solid rgba(255,255,255,0.1); padding: 8px 15px; border-radius: 8px; cursor: pointer; }
        .btn-detail:hover { background: var(--accent); color: #000; border-color: var(--accent); }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); backdrop-filter: blur(10px); z-index: 1000; justify-content: center; align-items: center; }
        .modal-content { background: #0a0a0c; width: 90%; max-width: 900px; max-height: 85vh; border-radius: 30px; border: 1px solid rgba(255,255,255,0.1); padding: 50px; overflow-y: auto; position: relative; }
        .close { position: absolute; top: 30px; right: 30px; font-size: 30px; cursor: pointer; color: #444; }
        .desc-box { background: rgba(255,255,255,0.02); padding: 30px; border-radius: 20px; line-height: 1.8; color: #ccc; }
        .btn-sync { background: var(--accent); color: #000; padding: 12px 25px; border-radius: 12px; border: none; font-weight: 700; cursor: pointer; text-decoration: none; display: inline-block; }
    </style>
</head>
<body>
    <nav class="navbar">
        <div style="font-size: 20px; font-weight: 800;">GOOX<span style="color:var(--accent)">COMMAND</span></div>
        <button class="btn-sync" onclick="sync()">Global GitHub Push</button>
    </nav>
    <div class="project-tabs">
        <div class="tab active" onclick="switchProj('nulledscripts')" id="t-nulled">NulledScripts.net</div>
        <div class="tab" onclick="switchProj('nullphpscript')" id="t-nullphp">NullPHPScript.com</div>
    </div>
    <div class="main">
        <div class="stats-grid">
            <div class="stat-card"><div class="label">Total Queue</div><div class="value" id="tot">0</div></div>
            <div class="stat-card"><div class="label">Processed</div><div class="value" id="done">0</div></div>
            <div class="stat-card"><div class="label">Active Demos</div><div class="value" id="active">0</div></div>
            <div class="stat-card"><div class="label">Blocks</div><div class="value" id="fail" style="color:#ff007a">0</div></div>
        </div>
        <div class="feed-wrap" id="item-list"></div>
    </div>
    <div id="modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeM()">&times;</span>
            <div id="m-body"></div>
        </div>
    </div>
    <script>
        let cur = 'nulledscripts';
        let all = {};
        async function load() {
            try { const res = await fetch('/api/stats'); all = await res.json(); render(); } catch(e){}
        }
        function render() {
            const d = all[cur]; if(!d) return;
            document.getElementById('tot').innerText = d.total;
            document.getElementById('done').innerText = d.done;
            document.getElementById('active').innerText = d.active_links;
            document.getElementById('fail').innerText = d.failures;
            const list = document.getElementById('item-list'); list.innerHTML = '';
            d.last_items.reverse().forEach(i => {
                const row = document.createElement('div'); row.className = 'item-row';
                const imgPath = i.image_local ? '/' + i.image_local : 'https://placehold.co/100x100/111/333?text=SYNC';
                row.innerHTML = `
                    <img src="${imgPath}" class="thumb" onerror="this.src='https://placehold.co/100x100/111/333?text=SYNC'">
                    <div><div class="title">${i.title || 'Scanning...'} ${i.ai_processed?'<span style="color:#9b59b6;font-size:10px">🤖 AI</span>':''}</div><div class="meta">${i.url.substring(0,60)}...</div></div>
                    <div><span class="badge" style="background:rgba(0,242,255,0.1);color:var(--accent)">${i.category}</span></div>
                    <div style="font-size:11px;color:${i.link_status=='Active'?'#00ffa3':'#555'}">${i.link_status || 'CHECKING'}</div>
                    <button class="btn-detail" onclick="showM('${i.id}')">Details</button>
                `;
                list.appendChild(row);
            });
        }
        async function showM(id) {
            const res = await fetch(`/api/details/${cur}/${id}`);
            const item = await res.json();
            
            let mirrorHtml = '';
            if (item.mirrors && item.mirrors.length > 0) {
                mirrorHtml = '<h4 style="margin-top:30px">Download Mirrors:</h4><div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">';
                item.mirrors.forEach(link => {
                    const domain = link.split('/')[2] || 'Download';
                    mirrorHtml += `<a href="${link}" target="_blank" class="btn-detail" style="text-align:center; text-decoration:none;">Download from ${domain}</a>`;
                });
                mirrorHtml += '</div>';
            } else if (item.download_url) {
                mirrorHtml = `<h4 style="margin-top:30px">Download Source:</h4>
                              <a href="${item.download_url}" target="_blank" class="btn-sync" style="width:100%; display:block; text-align:center;">Download Now</a>`;
            }

            const imgPath = item.image_local ? '/' + item.image_local : 'https://placehold.co/800x400/111/333?text=Image%20Syncing...';
            document.getElementById('m-body').innerHTML = `
                <img src="${imgPath}" style="width:100%;border-radius:20px;margin-bottom:20px" onerror="this.src='https://placehold.co/800x400/111/333?text=Image%20Syncing...'">
                <h1>${item.title}</h1>
                <div class="desc-box">${item.description_html}</div>
                ${mirrorHtml}
                <div style="margin-top:30px;display:flex;gap:10px;border-top:1px solid rgba(255,255,255,0.05);padding-top:20px;">
                    <a href="${item.url}" target="_blank" class="btn-detail" style="flex:1;text-align:center;text-decoration:none;">View Original</a>
                    <a href="${item.preview_url}" target="_blank" class="btn-sync" style="flex:1;text-align:center;background:#f1c40f">Live Demo</a>
                </div>
            `;
            document.getElementById('modal').style.display = 'flex';
        }
        function closeM() { document.getElementById('modal').style.display = 'none'; }
        function switchProj(p) { cur = p; document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active')); document.getElementById('t-'+(p=='nulledscripts'?'nulled':'nullphp')).classList.add('active'); render(); }
        async function sync() { const res = await fetch('/api/push/github',{method:'POST'}); const d = await res.json(); alert(d.message); }
        setInterval(load, 3000); load();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(port=5001, host="0.0.0.0")
