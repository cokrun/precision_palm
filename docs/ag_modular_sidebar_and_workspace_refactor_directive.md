# DIRECTIVE RESMI AG: REFAKTORISASI MODULAR UI/UX ENTERPRISE (SIDEBAR + TOP CONTEXT BAR + 3 SUB-VIEW TABS)

**Status:** Perintah Implementasi Frontend & Routing Non-Destruktif (Safe Modular Refactoring)  
**Aturan Utama:** JANGAN BUAT FOLDER BARU. JANGAN COPY-PASTE DARI AWAL. Pertahankan seluruh file Python, JS, dan database SQLite yang sudah ada. Cukup tambahkan komponen modular partial Jinja2 dan perbarui wadah pembungkus layout.

---

## 1. BUAT DUA FILE PARTIAL BARU DI `templates/partials/`

### A. Buat `templates/partials/top_context_bar.html`
Bilah sticky di bagian paling atas workspace kanan yang menampilkan konteks aktif:
* Dropdown Dossier Perusahaan Aktif (misal: `EST-MDN-001 • PT Mandailing Agro Sustainable`).
* Dropdown Tahun Audit (misal: `2026 (Active Statutory Audit Cycle)`).
* Toggle Yurisdiksi Pasar (`🇮🇩 Domestic IDR` vs `🌐 Export USD`).
* Lencana Kriptografis (`🔒 SHA-256 Valid • BigQuery Sync Active`).

### B. Buat `templates/partials/sidebar.html`
Sidebar vertikal kiri bergaya Google Cloud Console (lebar 240px, dapat diciutkan ke 64px):
* Logo: `🌴 Precision Palm Cloud OS`
* Menu Beranda: `/` (Executive Overview)
* Menu Tahap 1: `/cadastral-onboarding` (Registrasi Lahan & HGU)
* Menu Tahap 2A: `/planetary-observatory` (Observasi Spasial GEE & Satelit)
* Menu Tahap 2B: `/in-silico` (Mesin Biofisika, Tanaman Sela & Harga TBS)
* Menu Tahap 3: `/quarterly-surveillance` (Surveilans Lapangan Q1–Q4 & Multi-Evidence)
* Menu Tahap 4: `/statutory-ratification` (Sidang Asesor & Paspor Ekspor EUDR)
* Menu Topologi: `/compliance-lineage` (Silsilah Kepatuhan 12-Simpul DAG)
* Menu Bawah: `/system-control` (Pusat Kendali Pengaturan)
* Tombol Toggle di bawah: `[ ◀ Minimized / Expanded ]` (Menyimpan state `collapsed` di `localStorage`).

---

## 2. MODIFIKASI WADAH HALAMAN UTAMA (SAFE WRAPPER)

Di file-file template utama (`templates/spatial.html`, `templates/simulator.html`, `templates/timelines.html`, `templates/roadmap.html`, `templates/topologi.html`):

Ganti pembungkus body menjadi layout flex 2-kolom:

```html
<!-- STRUKTUR LAYOUT ENTERPRISE BARU -->
<body class="bg-slate-950 text-slate-100 font-sans min-h-screen flex antialiased">

    <!-- 1. SIDEBAR KIRI MODULAR -->
    {% include 'partials/sidebar.html' %}

    <!-- 2. WORKSPACE UTAMA KANAN -->
    <div id="mainWorkspaceContainer" class="flex-1 flex flex-col min-w-0 transition-all duration-300">
        
        <!-- Sticky Top Context Bar -->
        {% include 'partials/top_context_bar.html' %}

        <!-- Isi Konten Spesifik Halaman (Kode yang sudah ada diletakkan di sini) -->
        <main class="flex-1 p-4 sm:p-6 lg:p-8 space-y-6 overflow-y-auto">
            <!-- ... KONTEN ASLI HALAMAN TANPA DIHAPUS ... -->
        </main>

        <!-- Footer Universal -->
        {% include 'partials/footer.html' ignore missing %}
    </div>

</body>

3. KHUSUS templates/simulator.html (/in-silico): ATASI HALAMAN PANJANG

    Pasang 3 Bilah Sub-Tab di Puncak Workspace:

HTML

   <div class="flex items-center gap-2 border-b border-slate-800 pb-2 font-mono text-xs">
       <button type="button" onclick="switchInSilicoTab('agronomy')" id="tabBtn_agronomy" class="px-4 py-2 rounded-xl bg-emerald-600 text-white font-bold cursor-pointer">
           🌿 1. Agronomic Intercrop & Root Buffer
       </button>
       <button type="button" onclick="switchInSilicoTab('financial')" id="tabBtn_financial" class="px-4 py-2 rounded-xl bg-slate-900 text-slate-400 hover:text-white cursor-pointer">
           💰 2. Commodity Pricing & Revenue (rumus_tb.py)
       </button>
       <button type="button" onclick="switchInSilicoTab('compliance')" id="tabBtn_compliance" class="px-4 py-2 rounded-xl bg-slate-900 text-slate-400 hover:text-white cursor-pointer">
           🛡️ 3. Land Sparing (LER) & Carbon Assets
       </button>
   </div>
   

    Bungkus Bagian 10-Year Cashflow dengan Tag Accordion Bawaan HTML:
    Cari bagian tabel 10-Year In-Silico Financial Cashflow & Natural Capital Valuation:
    Bungkus menggunakan <details class="group bg-slate-900 border border-slate-800 rounded-2xl p-4">:

HTML

   <details class="group bg-slate-900/90 border border-slate-800 rounded-2xl p-4 transition-all">
       <summary class="flex items-center justify-between cursor-pointer font-mono text-xs font-bold text-slate-300 select-none">
           <span class="flex items-center gap-2">
               <span>📊</span> <span>10-Year In-Silico Financial Cashflow & Natural Capital Projection (Click to Expand / Collapse)</span>
           </span>
           <span class="text-cyan-400 group-open:rotate-180 transition-transform text-sm">▼</span>
       </summary>
       <div class="pt-4 border-t border-slate-800 mt-3 overflow-x-auto">
           <!-- Tabel 10-Year Cashflow Asli Diletakkan di Sini -->
       </div>
   </details>
   

Secara default, tabel tertutup rapi sehingga pengguna tidak perlu menggulung layar panjang ke bawah!
4. DUAL-ROUTING DI app.py (BEBAS 404 BROKEN LINKS)

Di file app.py, tambahkan rute-rute baru berdampingan dengan rute lama:
Python

# STREAMING_CHUNK:Adding enterprise routes with dual-routing and 301 redirects
# ==============================================================================
# ENTERPRISE ROUTES (INTERNATIONAL NOMENCLATURE)
# ==============================================================================

@app.route('/in-silico')
def render_in_silico_engine():
    return render_template('simulator.html')

@app.route('/planetary-observatory')
def render_planetary_observatory():
    return render_template('spatial.html')

@app.route('/quarterly-surveillance')
def render_quarterly_surveillance():
    return render_template('timelines.html')

@app.route('/statutory-ratification')
def render_statutory_ratification():
    return render_template('roadmap.html')

@app.route('/compliance-lineage')
def render_compliance_lineage():
    return render_template('topologi.html')

@app.route('/concession-register')
def render_concession_register():
    return render_template('pendaftaran.html')

@app.route('/cadastral-onboarding')
def render_cadastral_onboarding():
    return render_template('permohonan.html')

@app.route('/system-control')
def render_system_control():
    return render_template('pengaturan.html')

# ==============================================================================
# PERMANENT REDIRECTS UNTUK MEMPERTAHANKAN TAUTAN LAMA
# ==============================================================================
@app.route('/proses')
def redirect_legacy_proses():
    return redirect(url_for('render_in_silico_engine'), code=301)

@app.route('/spatial')
def redirect_legacy_spatial():
    return redirect(url_for('render_planetary_observatory'), code=301)

@app.route('/timelines')
def redirect_legacy_timelines():
    return redirect(url_for('render_quarterly_surveillance'), code=301)

@app.route('/roadmap')
def redirect_legacy_roadmap():
    return redirect(url_for('render_statutory_ratification'), code=301)

@app.route('/topologi')
def redirect_legacy_topologi():
    return redirect(url_for('render_compliance_lineage'), code=301)