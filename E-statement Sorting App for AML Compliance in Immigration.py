import os
import re
import shutil
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from datetime import datetime
from pypdf import PdfReader, PdfWriter
import patoolib  # Library pembaca arsip (zip, rar, 7z)

# Mapping nama bulan
MONTH_MAP = {
    'januari': 1, 'january': 1, 'jan': 1,
    'februari': 2, 'february': 2, 'feb': 2,
    'maret': 3, 'march': 3, 'mar': 3,
    'april': 4, 'apr': 4,
    'mei': 5, 'may': 5,
    'juni': 6, 'june': 6, 'jun': 6,
    'juli': 7, 'july': 7, 'jul': 7,
    'agustus': 8, 'august': 8, 'agu': 8, 'aug': 8,
    'september': 9, 'sep': 9,
    'oktober': 10, 'october': 10, 'okt': 10, 'oct': 10,
    'november': 11, 'nov': 11,
    'desember': 12, 'december': 12, 'des': 12, 'dec': 12
}

BANK_IDENTIFIERS = {
    "Bank BCA": ["bank central asia", "bca", "klikbca", "mybca"],
    "Bank Mandiri": ["bank mandiri", "mandiri", "livin"],
    "Bank BRI": ["bank rakyat indonesia", "bri", "brimo"],
    "Bank BNI": ["bank negara indonesia", "bni"],
    "CIMB Niaga": ["cimb niaga", "octo mobile", "cimb"],
    "Bank Jago": ["bank jago", "pt bank jago"],
    "Jenius (BTPN)": ["jenius", "btpn"]
}

BROKER_IDENTIFIERS = ["metatrader", "mt4", "mt5", "interactive brokers", "exness", "xm", "octa", "fxpro", "ic markets", "fbs", "oanda"]


# ==================== ARCHIVE & FILE PROCESSOR ====================

def process_input_files(file_paths):
    """Ekstrak file arsip (.zip, .rar, .7z) jika ada dan kembalikan semua path PDF."""
    extracted_pdf_paths = []
    temp_dirs = []

    for p in file_paths:
        ext = os.path.splitext(p)[1].lower()

        if ext == ".pdf":
            extracted_pdf_paths.append(p)
        elif ext in [".zip", ".rar", ".7z"]:
            try:
                temp_dir = tempfile.mkdtemp(prefix="doc_unpacker_")
                temp_dirs.append(temp_dir)
                patoolib.extract_archive(p, outdir=temp_dir, verbosity=-1)

                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        if file.lower().endswith(".pdf"):
                            extracted_pdf_paths.append(os.path.join(root, file))
            except Exception as e:
                print(f"Gagal mengekstrak {p}: {e}")

    return extracted_pdf_paths, temp_dirs


# ==================== SMART PASSWORD CHECKER ====================

def check_and_unlock_pdf(pdf_path, category_name="Dokumen"):
    """
    Cek apakah PDF terenkripsi.
    Coba dekripsi otomatis dengan password kosong ("") di balik layar.
    Jika gagal (memang butuh password), baru tampilkan pop-up.
    """
    try:
        reader = PdfReader(pdf_path)
        filename = os.path.basename(pdf_path)

        if reader.is_encrypted:
            # 1. SILENT LOGIN: Coba pass kosong dulu (Owner restriction)
            try:
                if reader.decrypt("") > 0:
                    return reader, True
            except Exception:
                pass

            # 2. Jika gagal, baru panggil pop-up!
            while True:
                pwd = simpledialog.askstring(
                    "🔐 File Terkunci Password",
                    f"File [{category_name}] ini dilindungi password:\n\n📄 {filename}\n\nMasukkan Password untuk membuka:",
                    show='*'
                )
                if pwd is None:  # User Cancel
                    return None, False

                try:
                    if reader.decrypt(pwd) > 0:
                        return reader, True
                    else:
                        messagebox.showerror("Error", "Password salah! Silakan coba lagi.")
                except Exception:
                    messagebox.showerror("Error", "Gagal membuka file dengan password tersebut.")
        else:
            return reader, True

    except Exception as e:
        print(f"Error checking PDF encryption: {e}")
        return None, False


# ==================== HYBRID PARSER FUNCTIONS ====================

def parse_statement_info(pdf_path, reader):
    """Membaca E-Statement Bank dengan Hybrid Matching (Filename First -> Content Fallback)."""
    bank_name = "Bank Lain / Tidak Dikenal"
    detected_dt = None
    filename = os.path.basename(pdf_path).lower()

    # LAYER 1: Cek Nama File
    for b_name, keywords in BANK_IDENTIFIERS.items():
        if any(kw in filename for kw in keywords):
            bank_name = b_name
            break

    try:
        first_page_text = reader.pages[0].extract_text() if len(reader.pages) > 0 else ""
        text_lower = first_page_text.lower()

        # LAYER 2: Jika dari Nama File gak ketemu, baru scan Isi PDF
        if bank_name == "Bank Lain / Tidak Dikenal":
            for b_name, keywords in BANK_IDENTIFIERS.items():
                if any(kw in text_lower for kw in keywords):
                    bank_name = b_name
                    break

        # TANGGAL / PERIODE (Cek Nama File Dulu)
        month_names = '|'.join(MONTH_MAP.keys())
        match_fn = re.search(rf'\b({month_names})\b.*?\b(\d{{4}})\b', filename)
        if match_fn:
            m_str, y_str = match_fn.groups()
            detected_dt = datetime(int(y_str), MONTH_MAP[m_str], 1)

        # Fallback ke Isi PDF
        if not detected_dt:
            match_text = re.search(rf'\b({month_names})\s+(\d{{4}})\b', text_lower)
            if match_text:
                m_str, y_str = match_text.groups()
                detected_dt = datetime(int(y_str), MONTH_MAP[m_str], 1)

        if not detected_dt:
            match_date = re.search(r'\b(\d{2})[-/](\d{2})[-/](\d{4})\b', text_lower)
            if match_date:
                _, month, year = match_date.groups()
                if 1 <= int(month) <= 12 and 1900 <= int(year) <= 2100:
                    detected_dt = datetime(int(year), int(month), 1)

    except Exception as e:
        print(f"Error reading Bank PDF: {e}")

    if not detected_dt:
        detected_dt = datetime.fromtimestamp(os.path.getmtime(pdf_path))

    return bank_name, detected_dt


def parse_spt_info(pdf_path, reader):
    """Membaca SPT Pajak Tahunan."""
    tax_year = 0
    spt_type = "SPT Tahunan"
    filename = os.path.basename(pdf_path).lower()

    try:
        first_page_text = reader.pages[0].extract_text() if len(reader.pages) > 0 else ""
        text_lower = first_page_text.lower()

        if "1770 s" in text_lower or "1770s" in filename: spt_type = "SPT 1770 S"
        elif "1770 ss" in text_lower or "1770ss" in filename: spt_type = "SPT 1770 SS"
        elif "1770" in text_lower or "1770" in filename: spt_type = "SPT 1770"
        elif "1771" in text_lower or "1771" in filename: spt_type = "SPT 1771 (Badan)"

        # Cek Tahun dari Filename Dulu
        match_fn = re.search(r'\b(20\d{2})\b', filename)
        if match_fn:
            tax_year = int(match_fn.group(1))

        # Fallback ke Isi PDF
        if tax_year == 0:
            match_year = re.search(r'(?:tahun pajak|pajak)\s*[:\s]*(\d{4})', text_lower)
            if match_year:
                tax_year = int(match_year.group(1))
            else:
                years_found = [int(y) for y in re.findall(r'\b(20\d{2})\b', text_lower)]
                if years_found:
                    tax_year = min(years_found)

    except Exception as e:
        print(f"Error reading SPT PDF: {e}")

    if tax_year == 0:
        tax_year = datetime.fromtimestamp(os.path.getmtime(pdf_path)).year

    return spt_type, tax_year


def parse_broker_info(pdf_path, reader):
    """Membaca Broker Statement."""
    broker_name = "Forex / Stock Broker"
    acc_id = "N/A"
    detected_dt = None
    filename = os.path.basename(pdf_path).lower()

    # Layer 1: Filename Check
    for b in BROKER_IDENTIFIERS:
        if b in filename:
            broker_name = b.upper()
            break

    try:
        first_page_text = reader.pages[0].extract_text() if len(reader.pages) > 0 else ""
        text_lower = first_page_text.lower()

        # Layer 2: Content Check
        if broker_name == "Forex / Stock Broker":
            for b in BROKER_IDENTIFIERS:
                if b in text_lower:
                    broker_name = b.upper()
                    break

        match_acc = re.search(r'(?:account|login|no\. rekening)\s*[:\s]*(\d{5,10})', text_lower)
        if match_acc:
            acc_id = match_acc.group(1)

        month_names = '|'.join(MONTH_MAP.keys())
        match_fn = re.search(rf'\b({month_names})\b.*?\b(\d{{4}})\b', filename)
        if match_fn:
            m_str, y_str = match_fn.groups()
            detected_dt = datetime(int(y_str), MONTH_MAP[m_str], 1)

        if not detected_dt:
            match_text = re.search(rf'\b({month_names})\s+(\d{{4}})\b', text_lower)
            if match_text:
                m_str, y_str = match_text.groups()
                detected_dt = datetime(int(y_str), MONTH_MAP[m_str], 1)

    except Exception as e:
        print(f"Error reading Broker PDF: {e}")

    if not detected_dt:
        detected_dt = datetime.fromtimestamp(os.path.getmtime(pdf_path))

    return broker_name, acc_id, detected_dt


# ==================== APPLICATION GUI ====================

class MasterImmigrationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Investor Immigration Doc Toolkit v5.2 (Hybrid Parser)")
        self.geometry("880x660")
        self.minsize(800, 550)

        self.style = ttk.Style(self)
        if "vista" in self.style.theme_names():
            self.style.theme_use("vista")
        elif "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.stmt_files = []
        self.spt_files = []
        self.broker_files = []
        self.active_temp_dirs = []

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._build_ui()

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        t1 = ttk.Frame(notebook, padding=10)
        notebook.add(t1, text=" 🏦 Bank Statements ")
        self._build_bank_tab(t1)

        t2 = ttk.Frame(notebook, padding=10)
        notebook.add(t2, text=" 📄 SPT Pajak ")
        self._build_spt_tab(t2)

        t3 = ttk.Frame(notebook, padding=10)
        notebook.add(t3, text=" 📈 Forex & Broker Statements ")
        self._build_broker_tab(t3)

    # ---------------- TAB BUILDERS ----------------
    def _build_bank_tab(self, parent):
        ttk.Label(parent, text="Bank E-Statement Merger (Hybrid Parser & Auto Password)", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        bf = ttk.Frame(parent)
        bf.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(bf, text="➕ Tambah File (PDF / RAR / ZIP)", command=self.add_bank_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(bf, text="🗑️ Clear", command=lambda: self.clear_list(self.stmt_files, self.tree_bank, self.lbl_bank_status)).pack(side=tk.LEFT)

        cols = ("bank", "period", "filename")
        self.tree_bank = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        self.tree_bank.heading("bank", text="Bank")
        self.tree_bank.heading("period", text="Periode")
        self.tree_bank.heading("filename", text="File Path")
        self.tree_bank.column("bank", width=150, anchor=tk.CENTER)
        self.tree_bank.column("period", width=150, anchor=tk.CENTER)
        self.tree_bank.column("filename", width=400)

        sc = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree_bank.yview)
        self.tree_bank.configure(yscroll=sc.set)
        self.tree_bank.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        sc.pack(side=tk.RIGHT, fill=tk.Y)

        btm = ttk.Frame(parent)
        btm.pack(fill=tk.X, pady=(10, 0))
        self.lbl_bank_status = ttk.Label(btm, text="Total File: 0")
        self.lbl_bank_status.pack(side=tk.LEFT)
        ttk.Button(btm, text="⚡ Merge Bank Statements", command=self.merge_bank_pdfs).pack(side=tk.RIGHT)

    def _build_spt_tab(self, parent):
        ttk.Label(parent, text="SPT Pajak Tahunan Merger (Hybrid Parser & Auto Password)", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        bf = ttk.Frame(parent)
        bf.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(bf, text="➕ Tambah File (PDF / RAR / ZIP)", command=self.add_spt_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(bf, text="🗑️ Clear", command=lambda: self.clear_list(self.spt_files, self.tree_spt, self.lbl_spt_status)).pack(side=tk.LEFT)

        cols = ("type", "year", "filename")
        self.tree_spt = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        self.tree_spt.heading("type", text="Jenis SPT")
        self.tree_spt.heading("year", text="Tahun Pajak")
        self.tree_spt.heading("filename", text="File Path")
        self.tree_spt.column("type", width=180, anchor=tk.CENTER)
        self.tree_spt.column("year", width=120, anchor=tk.CENTER)
        self.tree_spt.column("filename", width=400)

        sc = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree_spt.yview)
        self.tree_spt.configure(yscroll=sc.set)
        self.tree_spt.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        sc.pack(side=tk.RIGHT, fill=tk.Y)

        btm = ttk.Frame(parent)
        btm.pack(fill=tk.X, pady=(10, 0))
        self.lbl_spt_status = ttk.Label(btm, text="Total File: 0")
        self.lbl_spt_status.pack(side=tk.LEFT)
        ttk.Button(btm, text="⚡ Merge SPT Pajak", command=self.merge_spt_pdfs).pack(side=tk.RIGHT)

    def _build_broker_tab(self, parent):
        ttk.Label(parent, text="Forex / Broker Statements Merger (Hybrid Parser & Auto Password)", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        bf = ttk.Frame(parent)
        bf.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(bf, text="➕ Tambah File (PDF / RAR / ZIP)", command=self.add_broker_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(bf, text="🗑️ Clear", command=lambda: self.clear_list(self.broker_files, self.tree_broker, self.lbl_broker_status)).pack(side=tk.LEFT)

        cols = ("broker", "acc", "period", "filename")
        self.tree_broker = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        self.tree_broker.heading("broker", text="Broker / Platform")
        self.tree_broker.heading("acc", text="Account No.")
        self.tree_broker.heading("period", text="Periode")
        self.tree_broker.heading("filename", text="File Path")
        
        self.tree_broker.column("broker", width=160, anchor=tk.CENTER)
        self.tree_broker.column("acc", width=120, anchor=tk.CENTER)
        self.tree_broker.column("period", width=130, anchor=tk.CENTER)
        self.tree_broker.column("filename", width=290)

        sc = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree_broker.yview)
        self.tree_broker.configure(yscroll=sc.set)
        self.tree_broker.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        sc.pack(side=tk.RIGHT, fill=tk.Y)

        btm = ttk.Frame(parent)
        btm.pack(fill=tk.X, pady=(10, 0))
        self.lbl_broker_status = ttk.Label(btm, text="Total Statement Trading: 0")
        self.lbl_broker_status.pack(side=tk.LEFT)
        ttk.Button(btm, text="⚡ Merge Broker Statements", command=self.merge_broker_pdfs).pack(side=tk.RIGHT)

    # ---------------- ADD FILE HANDLERS ----------------
    def _prompt_and_unpack(self):
        paths = filedialog.askopenfilenames(
            title="Pilih PDF atau File Arsip (ZIP/RAR/7Z)",
            filetypes=[
                ("All Supported Files", "*.pdf *.zip *.rar *.7z"),
                ("PDF Files", "*.pdf"),
                ("Archive Files", "*.zip *.rar *.7z")
            ]
        )
        if not paths: return []

        pdf_paths, t_dirs = process_input_files(paths)
        self.active_temp_dirs.extend(t_dirs)
        return pdf_paths

    def add_bank_files(self):
        all_pdfs = self._prompt_and_unpack()
        for p in all_pdfs:
            if not any(x['path'] == p for x in self.stmt_files):
                reader, success = check_and_unlock_pdf(p, category_name="Bank E-Statement")
                if success and reader:
                    bank, dt = parse_statement_info(p, reader)
                    self.stmt_files.append({'path': p, 'reader': reader, 'bank': bank, 'period_dt': dt, 'filename': os.path.basename(p)})
        self.stmt_files.sort(key=lambda x: (x['bank'], x['period_dt']))
        self._refresh_tree(self.stmt_files, self.tree_bank, self.lbl_bank_status, lambda i: (i['bank'], i['period_dt'].strftime("%B %Y"), i['filename']))

    def add_spt_files(self):
        all_pdfs = self._prompt_and_unpack()
        for p in all_pdfs:
            if not any(x['path'] == p for x in self.spt_files):
                reader, success = check_and_unlock_pdf(p, category_name="SPT Pajak")
                if success and reader:
                    stype, year = parse_spt_info(p, reader)
                    self.spt_files.append({'path': p, 'reader': reader, 'type': stype, 'year': year, 'filename': os.path.basename(p)})
        self.spt_files.sort(key=lambda x: x['year'])
        self._refresh_tree(self.spt_files, self.tree_spt, self.lbl_spt_status, lambda i: (i['type'], i['year'], i['filename']))

    def add_broker_files(self):
        all_pdfs = self._prompt_and_unpack()
        for p in all_pdfs:
            if not any(x['path'] == p for x in self.broker_files):
                reader, success = check_and_unlock_pdf(p, category_name="Broker Statement")
                if success and reader:
                    broker, acc, dt = parse_broker_info(p, reader)
                    self.broker_files.append({'path': p, 'reader': reader, 'broker': broker, 'acc': acc, 'period_dt': dt, 'filename': os.path.basename(p)})
        self.broker_files.sort(key=lambda x: (x['broker'], x['acc'], x['period_dt']))
        self._refresh_tree(self.broker_files, self.tree_broker, self.lbl_broker_status, lambda i: (i['broker'], i['acc'], i['period_dt'].strftime("%B %Y"), i['filename']))

    def _refresh_tree(self, data_list, tree, lbl, val_func):
        for r in tree.get_children(): tree.delete(r)
        for item in data_list:
            tree.insert("", tk.END, values=val_func(item))
        lbl.config(text=f"Total File: {len(data_list)}")

    def clear_list(self, data_list, tree, lbl):
        data_list.clear()
        self._refresh_tree(data_list, tree, lbl, lambda x: ())

    # ---------------- MERGE METHODS ----------------
    def merge_generic(self, data_list, default_filename, bookmark_fmt):
        if not data_list:
            messagebox.showwarning("Kosong", "Tidak ada file yang dipilih!")
            return

        save_path = filedialog.asksaveasfilename(
            title="Simpan File Master PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile=default_filename
        )
        if not save_path: return

        try:
            writer = PdfWriter()
            page_count = 0
            for item in data_list:
                reader = item['reader']
                title = bookmark_fmt(item)
                writer.add_outline_item(title=title, page_number=page_count)
                for page in reader.pages:
                    writer.add_page(page)
                    page_count += 1

            with open(save_path, "wb") as f:
                writer.write(f)
            messagebox.showinfo("Sukses!", f"Berhasil membuat {default_filename} dengan {len(data_list)} file terurut dan ter-bookmark!")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menggabungkan PDF: {e}")

    def merge_bank_pdfs(self):
        self.merge_generic(self.stmt_files, "Master_Bank_Statements.pdf", lambda i: f"{i['bank']} - {i['period_dt'].strftime('%B %Y')}")

    def merge_spt_pdfs(self):
        self.merge_generic(self.spt_files, "Master_SPT_Tahunan.pdf", lambda i: f"{i['type']} - Tahun {i['year']}")

    def merge_broker_pdfs(self):
        self.merge_generic(self.broker_files, "Master_Trading_Broker_Statements.pdf", lambda i: f"{i['broker']} (Acc:{i['acc']}) - {i['period_dt'].strftime('%B %Y')}")

    def on_closing(self):
        for td in self.active_temp_dirs:
            if os.path.exists(td):
                try:
                    shutil.rmtree(td)
                except Exception:
                    pass
        self.destroy()


if __name__ == "__main__":
    app = MasterImmigrationApp()
    app.mainloop()