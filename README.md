# E-statement-Manager
E-statement Manager.exe — Standalone offline app to automatically decrypt, sort, and merge bank/tax/broker statements into a single bookmarked Master PDF for investor visa &amp; AML audit compliance.
# ✈️ E-statement Manager (v5.2)

![Version](https://img.shields.io/badge/Version-5.2%20Standalone-blue?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20Executable%20(.exe)-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-orange?style=flat-square)

---

### 🇮🇩 / 🇬🇧 About The Application / Tentang Aplikasi

**E-statement Manager** is a lightweight, standalone desktop executable (`E-statement Manager.exe`) designed for investor visa applicants, wealth compliance audits, and Anti-Money Laundering (AML) proof-of-funds verification. It automates PDF decryption, metadata parsing, chronological sorting, and master PDF compilation.

**E-statement Manager** adalah aplikasi desktop *standalone* (`E-statement Manager.exe`) yang dirancang khusus untuk pemohon visa investor, audit kepatuhan aset, dan verifikasi *proof-of-funds* (AML). Aplikasi ini mengotomatisasi dekripsi PDF, pembacaan metadata, pengurutan kronologis, serta penggabungan PDF Master secara terstruktur.

---

### 🌟 Key Features / Fitur Utama

*   **🔐 Smart Password Auto-Detector & Silent Unlocker**
    *   **[EN]** Tests PDF encryption automatically. Silently unlocks dummy permission locks (*empty passwords*) without annoying pop-ups. Prompts appear only when genuine user passwords (e.g., DOB/Tax ID) are required.
    *   **[ID]** Menguji enkripsi PDF secara otomatis. Membuka *permission lock* palsu (*empty password*) secara otomatis tanpa pop-up. Pop-up hanya muncul jika file benar-benar terkunci password rahasia (seperti NPWP/Tanggal Lahir).
*   **🧠 Dual-Layer Hybrid Parser System**
    *   **[EN]** Prevents misclassification by evaluating file names first before falling back to page content scanning. (e.g., BNI e-statements containing transfer references to BCA won't be misidentified as BCA).
    *   **[ID]** Mencegah salah identifikasi dengan memeriksa nama file terlebih dahulu sebelum memindai isi halaman. (Misal: e-statement BNI yang memiliki histori transfer ke BCA tidak akan keliru dikelompokkan sebagai BCA).
*   **📦 Direct Archive Processing (.zip / .rar / .7z)**
    *   **[EN]** Extracts and processes compressed document archives directly on the fly without manual pre-extraction.
    *   **[ID]** Mengekstrak dan memproses file arsip dokumen secara langsung tanpa perlu diekstrak manual terlebih dahulu.
*   **📅 Automatic Chronological Sorting**
    *   **[EN]** Detects document periods (months and years) and arranges them in exact chronological sequence (Jan -> Dec).
    *   **[ID]** Mendeteksi periode dokumen (bulan dan tahun) lalu mengurutkannya secara runtut sesuai urutan waktu (Jan -> Des).
*   **🔖 Automatic PDF Outlines & Bookmarks**
    *   **[EN]** Generates a Master PDF equipped with structured sidebar bookmarks per bank/broker and period—highly favored by immigration officers, AML auditors, and sworn translators.
    *   **[ID]** Menghasilkan Master PDF yang dilengkapi *bookmark* navigasi di sidebar per bank/broker dan periode—sangat disukai oleh petugas imigrasi, auditor AML, dan penerjemah tersumpah.
*   **🔒 100% Offline & Private**
    *   **[EN]** Runs completely locally on your computer with zero web uploads, ensuring total security for sensitive banking data.
    *   **[ID]** Berjalan 100% lokal di komputer tanpa *upload* ke server web, menjamin keamanan penuh data finansial sensitif.

---

### 📂 Supported Documents / Dokumen yang Didukung

1.  **Bank E-Statements:** BCA, Mandiri, BNI, BRI, CIMB Niaga, Bank Jago, Jenius (BTPN), etc.
2.  **Annual Tax Returns / SPT Pajak:** Indonesia Tax Forms 1770, 1770 S, 1770 SS, & 1771 (Corporate).
3.  **Forex & Broker Statements:** MetaTrader 4 (MT4), MetaTrader 5 (MT5), Interactive Brokers (IBKR), Exness, XM, Octa, IC Markets, etc.

---

### 🚀 How to Run / Cara Penggunaan

#### Standalone Executable / Mode Aplikasi (.exe)
1.  Run / Jalankan **`E-statement Manager.exe`** directly (No Python installation required / Tidak memerlukan instalasi Python).
2.  Select the desired document category tab / Pilih tab kategori dokumen (**Bank Statements**, **SPT Pajak**, or **Broker Statements**).
3.  Click **➕ Tambah File** to add PDF files or archive files (`.zip`, `.rar`, `.7z`).
4.  The application automatically unlocks, parses, and orders your files chronologically.
5.  Click **⚡ Merge** to export a single, beautifully organized, bookmarked **Master PDF**.

---

### 🛠️ Tech Stack & Dependencies / Stack Teknologi

*   **Executable Format:** Windows Standalone `.exe` (PyInstaller)
*   **GUI Engine:** Python `tkinter` & `ttk`
*   **PDF Engine:** `pypdf` (PdfReader, PdfWriter)
*   **Archive Engine:** `patoolib` (7-Zip / UnRAR backend)

---

### 📄 License / Lisensi

This project is licensed under the [MIT License](LICENSE).
