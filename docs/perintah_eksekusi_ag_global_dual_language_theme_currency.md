# INSTRUKSI EKSEKUSI RESMI UNTUK AG: PENEGAKAN GLOBAL DUAL BAHASA (EN DEFAULT), LIGHT/DARK MODE & OTOMASI MATA UANG

**Perihal:** Implementasi Penyelarasan Global untuk Bahasa Inggris (`en`), Pengaitan Mata Uang (`USD` / `IDR`), dan Toggle Tema Light/Dark di Seluruh Halaman.  
**Dasar Acuan:** 
* `templates/partials/top_context_bar.html`
* `static/js/i18n.js`

---

## 📌 RINGkASAN PERINTAH KERJA (OBJECTIVES)
1. **Default Bahasa Inggris (`en`):**  
   Setiap halaman Flask saat pertama kali dibuka wajib menggunakan **Bahasa Inggris (`en`)** dan mata uang **`USD ($)`** secara otomatis.
2. **Kopel Bahasa & Mata Uang:**
   * Pengguna memilih **`EN`** &rarr; Mata uang otomatis beralih ke **`USD ($)`**.
   * Pengguna memilih **`ID`** &rarr; Mata uang otomatis beralih ke **`IDR (Rp)`**.
3. **Penyimpanan Status (*Persistence*):**  
   Preferensi tema (`dark` / `light`) dan bahasa (`en` / `id`) wajib disimpan di `localStorage` dan dibaca serentak oleh seluruh halaman template (`index.html`, `pendaftaran.html`, `spatial.html`, `simulator.html`, `timelines.html`, `roadmap.html`, `topologi.html`, `overview.html`, dll.).

---

## 🛠️ TUGAS 1: PASTIKAN `static/js/i18n.js` MENDUKUNG EN DEFAULT & EVENT BROADCAST

Pastikan file `static/js/i18n.js` memiliki logika inisialisasi default ke `en`:

```javascript
// static/js/i18n.js
(function () {
    const STORAGE_KEY = 'precision_palm_lang';
    
    function getStoredLang() {
        return localStorage.getItem(STORAGE_KEY) || 'en'; // Default strictly 'en'
    }

    function setStoredLang(lang) {
        const validated = (lang === 'id' || lang === 'en') ? lang : 'en';
        localStorage.setItem(STORAGE_KEY, validated);
        localStorage.setItem('precision_palm_language', validated);
        document.documentElement.lang = validated;
        return validated;
    }

    window.getAppLanguage = function() {
        return getStoredLang();
    };

    window.setAppLanguage = function(lang) {
        const l = setStoredLang(lang);
        if (typeof window.applyTranslations === 'function') {
            window.applyTranslations();
        }
        window.dispatchEvent(new CustomEvent('languagechanged', { detail: { lang: l } }));
    };

    // Auto-apply on load
    document.addEventListener('DOMContentLoaded', () => {
        const cur = getStoredLang();
        document.documentElement.lang = cur;
        if (typeof window.applyTranslations === 'function') {
            window.applyTranslations();
        }
    });
})();

🛠️ TUGAS 2: INTEGRASI PERSISTENSI TEMA DI SETIAP HALAMAN

Pastikan setiap file template utama (overview.html, pendaftaran.html, spatial.html, simulator.html, timelines.html, roadmap.html, topologi.html, dll.) menyertakan skrip inisialisasi tema sebelum <body> dirender untuk mencegah kedipan putih (FOUC):
HTML

<script>
    (function () {
        try {
            const savedTheme = localStorage.getItem('precision_palm_theme') || 'dark';
            if (savedTheme === 'light') {
                document.documentElement.classList.remove('dark');
            } else {
                document.documentElement.classList.add('dark');
            }
        } catch (_) {}
    })();
</script>

🧪 PENGUJIAN AKHIR OLEH AG

Jalankan server Flask:
Bash

python app.py

    Uji Default Clean Session (Mode Incognito):

        Buka http://localhost:8080/ → pastikan antarmuka tampil dalam Bahasa Inggris (en) dan mata uang USD ($).

    Uji Tombol Bahasa & Mata Uang:

        Klik tombol ID → teks berubah ke Bahasa Indonesia dan mata uang otomatis menjadi IDR (Rp).

        Pindah halaman (misalnya ke /overview atau /spatial) → pastikan pilihan bahasa dan mata uang tetap tersimpan konsisten.

    Uji Tombol Light / Dark Mode:

        Klik ikon 🌙 / ☀️ di top context bar → seluruh latar belakang dan kontras teks beralih mulus tanpa error.

