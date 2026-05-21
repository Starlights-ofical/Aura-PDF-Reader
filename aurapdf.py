import sys
import os
import json

# Uygulama başlatılırken oluşabilecek kütüphane eksikliği hatalarını yakalamak için ön yükleyici
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    import fitz  # PyMuPDF
    from PIL import Image, ImageTk, ImageDraw
    import customtkinter as ctk
except ModuleNotFoundError as e:
    # Eğer kritik bir kütüphane eksikse, kullanıcıya bunu bildiren şık bir kutu gösteriyoruz
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    missing_module = str(e).split("'")[-2] if "'" in str(e) else str(e)
    messagebox.showerror(
        "Eksik Kütüphane Hatası",
        f"Aura PDF Reader başlatılamadı çünkü sisteminizde gerekli bir kütüphane eksik:\n\n"
        f"Eksik Kütüphane: '{missing_module}'\n\n"
        f"Lütfen komut satırını (Terminal/CMD) açıp şu komutu çalıştırarak yükleyin:\n"
        f"pip install customtkinter pymupdf Pillow\n\n"
        f"Yükleme bittikten sonra uygulamayı tekrar çalıştırabilirsiniz."
    )
    sys.exit(1)
except Exception as e:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Başlatma Hatası", f"Program başlatılırken beklenmedik bir sistem hatası oluştu:\n{e}")
    sys.exit(1)

# Uygulama Tema Ayarları
ctk.set_appearance_mode("System")  # Sistem temasına göre otomatik (Dark/Light) ayarlanır
ctk.set_default_color_theme("blue")  # Tema rengi
RECENT_FILES_PATH = "recent_pdfs.json"

def get_aura_logo_image():
    """Bellekte şık, modern bir vektörel logo (PIL Image) oluşturur ve döndürür.
    Böylece diske yazma izni (PermissionError) hataları tamamen engellenir."""
    # 256x256 boyutlarında şeffaf bir tuval oluştur
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Arka plana modern bir dairesel gradyan havası ver
    for r in range(120, 0, -1):
        factor = r / 120
        r_color = int(124 - (124 - 30) * factor)
        g_color = int(58 + (219 - 58) * factor)
        b_color = int(237 + (254 - 237) * factor)
        draw.ellipse([128 - r, 128 - r, 128 + r, 128 + r], fill=(r_color, g_color, b_color, 255))
        
    # Üzerine şık bir kağıt/belge katlaması çiz
    draw.rounded_rectangle([75, 65, 181, 191], radius=14, fill=(255, 255, 255, 245))
    
    # Belge içi minimalist satırlar
    draw.rounded_rectangle([95, 105, 161, 115], radius=3, fill=(124, 58, 237, 255))
    draw.rounded_rectangle([95, 130, 145, 140], radius=3, fill=(30, 144, 255, 255))
    draw.rounded_rectangle([95, 155, 155, 165], radius=3, fill=(124, 58, 237, 255))
    
    return img

class ModernPDFReader(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Logo görselini bellekte oluştur
        self.logo_img = get_aura_logo_image()
        
        # Pencere Özellikleri
        self.title("Aura PDF Reader")
        self.geometry("1200x800")
        self.minsize(950, 650)
        
        try:
            # Bellekteki logoyu pencere ikonu (Taskbar / Windows) olarak ayarla
            self.tk_icon = ImageTk.PhotoImage(self.logo_img)
            self.iconphoto(False, self.tk_icon)
        except Exception:
            pass # Platform uyumsuzluklarını sessizce geç
            
        # Değişkenler
        self.doc = None
        self.current_page = 0
        self.zoom = 1.5
        self.rotation = 0
        self.file_path = ""
        self.recent_files = self.load_recent_files()
        self.sidebar_visible = True
        
        # Ana Taşıyıcı Frame
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        
        # Karşılama Ekranını Başlat
        self.show_welcome_screen()

    def load_recent_files(self):
        """Son kullanılan dosyaların listesini JSON dosyasından yükler."""
        if os.path.exists(RECENT_FILES_PATH):
            try:
                with open(RECENT_FILES_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_recent_file(self, path):
        """Açılan yeni bir PDF dosyasını son kullanılanlar listesine ekler."""
        if not path:
            return
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:5]  # En son 5 dosya
        
        try:
            with open(RECENT_FILES_PATH, "w", encoding="utf-8") as f:
                json.dump(self.recent_files, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def show_welcome_screen(self):
        """Uygulamanın şık ana karşılama panelini oluşturur."""
        for widget in self.main_container.winfo_children():
            widget.destroy()
            
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)
        
        # Karşılama Ekranı Ana Yapısı
        self.welcome_frame = ctk.CTkFrame(self.main_container, corner_radius=18)
        self.welcome_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.8)
        
        self.welcome_frame.grid_columnconfigure(0, weight=1)
        self.welcome_frame.grid_columnconfigure(1, weight=1)
        
        # --- Sol Kısım: Tanıtım ve Logo ---
        left_panel = ctk.CTkFrame(self.welcome_frame, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Program Logosu (Bellekten doğrudan yükleniyor)
        try:
            self.welcome_logo = ctk.CTkImage(light_image=self.logo_img, dark_image=self.logo_img, size=(140, 140))
            self.logo_lbl = ctk.CTkLabel(left_panel, image=self.welcome_logo, text="")
            self.logo_lbl.pack(pady=(40, 10))
        except Exception as e:
            print(f"Logo yüklenirken hata oluştu: {e}")
            
        self.logo_label = ctk.CTkLabel(
            left_panel, 
            text="Aura PDF", 
            font=ctk.CTkFont(family="Helvetica", size=42, weight="bold")
        )
        self.logo_label.pack(pady=5)
        
        self.subtitle_label = ctk.CTkLabel(
            left_panel, 
            text="Hızlı, modern ve minimalist PDF deneyimi", 
            font=ctk.CTkFont(family="Helvetica", size=14),
            text_color="gray"
        )
        self.subtitle_label.pack(pady=(0, 25))
        
        self.btn_large_open = ctk.CTkButton(
            left_panel,
            text="Bir PDF Belgesi Açın",
            font=ctk.CTkFont(family="Helvetica", size=16, weight="bold"),
            height=45,
            width=220,
            corner_radius=10,
            command=self.open_pdf
        )
        self.btn_large_open.pack(pady=10)
        
        # --- Sağ Kısım: Son Kullanılan Dosyalar ---
        right_panel = ctk.CTkFrame(self.welcome_frame, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=25)
        
        recent_title = ctk.CTkLabel(
            right_panel, 
            text="Son Kullanılan Belgeler", 
            font=ctk.CTkFont(family="Helvetica", size=18, weight="bold")
        )
        recent_title.pack(anchor="w", pady=(20, 15))
        
        if not self.recent_files:
            empty_lbl = ctk.CTkLabel(
                right_panel, 
                text="Henüz açılmış bir belge yok.\nHızlıca başlamak için soldaki butonu kullanın.", 
                font=ctk.CTkFont(size=13),
                text_color="gray",
                justify="left"
            )
            empty_lbl.pack(anchor="w", pady=20)
        else:
            for file_path in self.recent_files:
                filename = os.path.basename(file_path)
                if len(filename) > 35:
                    filename = filename[:32] + "..."
                
                file_btn = ctk.CTkButton(
                    right_panel,
                    text=f"📄  {filename}",
                    font=ctk.CTkFont(size=13),
                    anchor="w",
                    fg_color="transparent",
                    text_color=("black", "white"),
                    hover_color=("gray85", "gray25"),
                    height=38,
                    command=lambda path=file_path: self.open_specific_pdf(path)
                )
                file_btn.pack(fill="x", pady=4)
                
        # Tema Ayarlayıcı
        self.theme_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        self.theme_frame.pack(side="bottom", pady=20)
        
        self.lbl_theme = ctk.CTkLabel(self.theme_frame, text="Görünüm Modu:", font=ctk.CTkFont(size=12))
        self.lbl_theme.pack(side="left", padx=10)
        
        self.theme_option = ctk.CTkOptionMenu(
            self.theme_frame,
            values=["Sistem", "Koyu", "Açık"],
            command=self.change_theme,
            width=110
        )
        self.theme_option.pack(side="left")
        self.theme_option.set("Sistem")

    def show_workspace(self):
        """Uygulamanın PDF okuma ekranını ve araç çubuklarını oluşturur."""
        for widget in self.main_container.winfo_children():
            widget.destroy()
            
        self.main_container.grid_columnconfigure(0, weight=0)  # Sol Panel (Sidebar)
        self.main_container.grid_columnconfigure(1, weight=4)  # PDF Alanı
        self.main_container.grid_rowconfigure(0, weight=1)
        
        # --- SOL SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self.main_container, corner_radius=0, width=270)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_propagate(False)
        
        self.lbl_side_title = ctk.CTkLabel(
            self.sidebar, 
            text="Aura PDF", 
            font=ctk.CTkFont(family="Helvetica", size=20, weight="bold")
        )
        self.lbl_side_title.pack(pady=(25, 5), padx=20, anchor="w")
        
        filename = os.path.basename(self.file_path)
        if len(filename) > 24:
            filename = filename[:21] + "..."
        self.lbl_file = ctk.CTkLabel(
            self.sidebar, 
            text=f"📂 {filename}", 
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        )
        self.lbl_file.pack(pady=(0, 20), padx=20, fill="x")
        
        # --- ARAMA BÖLÜMÜ ---
        self.search_label = ctk.CTkLabel(self.sidebar, text="BELGE İÇİNDE ARA", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray")
        self.search_label.pack(padx=20, anchor="w", pady=(10, 3))
        
        self.search_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.search_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Kelime yazın...", height=30)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.search_entry.bind("<Return>", lambda event: self.render_page())
        
        self.btn_search = ctk.CTkButton(self.search_frame, text="Ara", width=50, height=30, command=self.render_page)
        self.btn_search.pack(side="right")
        
        # --- NAVİGASYON BÖLÜMÜ ---
        self.nav_label = ctk.CTkLabel(self.sidebar, text="SAYFA GEÇİŞLERİ", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray")
        self.nav_label.pack(padx=20, anchor="w", pady=(10, 3))
        
        self.btn_next = ctk.CTkButton(self.sidebar, text="Sonraki Sayfa ➡️", command=self.next_page, height=35)
        self.btn_next.pack(pady=4, padx=20, fill="x")
        
        self.btn_prev = ctk.CTkButton(self.sidebar, text="⬅️ Önceki Sayfa", command=self.prev_page, height=35, fg_color="gray", hover_color="#555555")
        self.btn_prev.pack(pady=4, padx=20, fill="x")
        
        self.goto_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.goto_frame.pack(fill="x", padx=20, pady=5)
        
        self.lbl_page = ctk.CTkLabel(self.goto_frame, text="Sayfa: -- / --", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_page.pack(side="left")
        
        self.btn_goto = ctk.CTkButton(self.goto_frame, text="Git", width=40, height=28, command=self.go_to_page)
        self.btn_goto.pack(side="right")
        
        self.entry_page = ctk.CTkEntry(self.goto_frame, width=45, height=28, justify="center")
        self.entry_page.pack(side="right", padx=5)
        self.entry_page.bind("<Return>", lambda event: self.go_to_page())
        
        # --- ARAÇLAR BÖLÜMÜ ---
        self.tools_label = ctk.CTkLabel(self.sidebar, text="ARAÇLAR", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray")
        self.tools_label.pack(padx=20, anchor="w", pady=(15, 3))
        
        self.rotate_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.rotate_frame.pack(fill="x", padx=20, pady=2)
        
        self.btn_rot_left = ctk.CTkButton(self.rotate_frame, text="🔄 Sola Döndür", command=self.rotate_left, height=32, fg_color="transparent", border_width=1)
        self.btn_rot_left.pack(side="left", fill="x", expand=True, padx=(0, 2))
        
        self.btn_rot_right = ctk.CTkButton(self.rotate_frame, text="🔄 Sağa Döndür", command=self.rotate_right, height=32, fg_color="transparent", border_width=1)
        self.btn_rot_right.pack(side="right", fill="x", expand=True, padx=(2, 0))
        
        self.btn_fullscreen = ctk.CTkButton(self.sidebar, text="🕶️ Odaklanma Modu (Tam Ekran)", command=self.toggle_fullscreen, height=32, fg_color="#10B981", hover_color="#059669")
        self.btn_fullscreen.pack(padx=20, fill="x", pady=5)
        
        # --- ZOOM BÖLÜMÜ ---
        self.zoom_label = ctk.CTkLabel(self.sidebar, text="YAKINLAŞTIRMA", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray")
        self.zoom_label.pack(padx=20, anchor="w", pady=(15, 3))
        
        self.zoom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.zoom_frame.pack(fill="x", padx=20, pady=2)
        
        self.btn_zoom_out = ctk.CTkButton(self.zoom_frame, text="-", width=45, height=32, command=self.zoom_out)
        self.btn_zoom_out.pack(side="left", padx=(0, 5))
        
        self.lbl_zoom = ctk.CTkLabel(self.zoom_frame, text=f"%{int(self.zoom*100)}", font=ctk.CTkFont(size=13))
        self.lbl_zoom.pack(side="left", expand=True)
        
        self.btn_zoom_in = ctk.CTkButton(self.zoom_frame, text="+", width=45, height=32, command=self.zoom_in)
        self.btn_zoom_in.pack(side="right", padx=(5, 0))
        
        self.btn_back = ctk.CTkButton(
            self.sidebar, 
            text="Ana Ekrana Dön", 
            command=self.show_welcome_screen, 
            fg_color="transparent", 
            border_width=1,
            height=35
        )
        self.btn_back.pack(side="bottom", pady=20, padx=20, fill="x")

        # --- SAĞ TARAF: PDF İZLEME ALANI ---
        self.viewer_frame = ctk.CTkFrame(self.main_container, corner_radius=0)
        self.viewer_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        self.canvas = tk.Canvas(self.viewer_frame, bg="#2b2b2b", highlightthickness=0)
        self.scroll_y = ctk.CTkScrollbar(self.viewer_frame, orientation="vertical", command=self.canvas.yview)
        self.scroll_x = ctk.CTkScrollbar(self.viewer_frame, orientation="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        
        self.viewer_frame.grid_rowconfigure(0, weight=1)
        self.viewer_frame.grid_rowconfigure(1, weight=0)
        self.viewer_frame.grid_columnconfigure(0, weight=1)
        self.viewer_frame.grid_columnconfigure(1, weight=0)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.scroll_x.grid(row=1, column=0, sticky="ew")
        
        # Fare tekerleği desteğini bağla
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
        self.render_page()

    def render_page(self):
        """Mevcut sayfayı netlik oranı, döndürme açısı ve arama vurgularıyla işleyip canvas'a basar."""
        if not self.doc:
            return
        try:
            canvas_bg = "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#e5e5e5"
            self.canvas.config(bg=canvas_bg)
            
            page = self.doc.load_page(self.current_page)
            page.set_rotation(self.rotation)
            
            mat = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=mat)
            
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Akıllı Metin Arama Vurgulama
            search_term = self.search_entry.get().strip() if hasattr(self, 'search_entry') else ""
            if search_term:
                rects = page.search_for(search_term)
                if rects:
                    img = img.convert("RGBA")
                    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                    draw = ImageDraw.Draw(overlay)
                    
                    for rect in rects:
                        x0 = rect.x0 * self.zoom
                        y0 = rect.y0 * self.zoom
                        x1 = rect.x1 * self.zoom
                        y1 = rect.y1 * self.zoom
                        draw.rectangle([x0, y0, x1, y1], fill=(255, 235, 59, 120), outline=(245, 124, 0, 200), width=1)
                    
                    img = Image.alpha_composite(img, overlay).convert("RGB")
            
            self.img_tk = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            
            canvas_width = self.canvas.winfo_width()
            x_pos = max((canvas_width - pix.width) // 2, 0) if canvas_width > pix.width else 0
            
            self.canvas.create_image(x_pos, 15, anchor=tk.NW, image=self.img_tk)
            self.canvas.config(scrollregion=(0, 0, max(pix.width, canvas_width), pix.height + 30))
            
            self.lbl_page.configure(text=f"Sayfa: {self.current_page + 1} / {len(self.doc)}")
            self.entry_page.delete(0, tk.END)
            self.entry_page.insert(0, str(self.current_page + 1))
            self.lbl_zoom.configure(text=f"%{int(self.zoom*100)}")
            
            self.btn_prev.configure(state="normal" if self.current_page > 0 else "disabled")
            self.btn_next.configure(state="normal" if self.current_page < len(self.doc) - 1 else "disabled")
            
        except Exception as e:
            messagebox.showerror("Render Hatası", f"Sayfa yüklenirken hata oluştu: {e}")

    def open_pdf(self):
        """Dosya seçici ile PDF açar."""
        file_path = filedialog.askopenfilename(filetypes=[("PDF Dosyaları", "*.pdf")])
        if not file_path:
            return
        self.open_specific_pdf(file_path)

    def open_specific_pdf(self, file_path):
        """Belirtilen yoldaki PDF'i yükler ve geçmişe ekler."""
        if not os.path.exists(file_path):
            messagebox.showerror("Hata", f"Belirtilen dosya bulunamadı:\n{file_path}")
            return
        try:
            self.file_path = file_path
            self.doc = fitz.open(file_path)
            self.current_page = 0
            self.rotation = 0
            self.zoom = 1.5
            self.save_recent_file(file_path)
            self.show_workspace()
        except Exception as e:
            messagebox.showerror("Hata", f"PDF yüklenirken bir sorun oluştu:\n{e}")

    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def next_page(self):
        if self.doc and self.current_page < len(self.doc) - 1:
            self.current_page += 1
            self.render_page()

    def go_to_page(self):
        """Kullanıcının girdiği sayfa numarasına gider."""
        if not self.doc:
            return
        try:
            page_num = int(self.entry_page.get()) - 1
            if 0 <= page_num < len(self.doc):
                self.current_page = page_num
                self.render_page()
            else:
                messagebox.showwarning("Geçersiz Sayfa", f"Lütfen 1 ile {len(self.doc)} arasında bir sayfa numarası girin.")
        except ValueError:
            messagebox.showwarning("Hata", "Lütfen geçerli bir sayı girin.")

    def zoom_in(self):
        if self.zoom < 4.0:
            self.zoom += 0.25
            self.render_page()

    def zoom_out(self):
        if self.zoom > 0.5:
            self.zoom -= 0.25
            self.render_page()

    def rotate_left(self):
        """Sayfayı sola (saat yönünün tersine) 90 derece döndürür."""
        self.rotation = (self.rotation - 90) % 360
        self.render_page()

    def rotate_right(self):
        """Sayfayı sağa (saat yönüne) 90 derece döndürür."""
        self.rotation = (self.rotation + 90) % 360
        self.render_page()

    def toggle_fullscreen(self):
        """Kenar çubuğunu gizleyerek odaklanma modunu açar/kapatır."""
        if self.sidebar_visible:
            self.sidebar.grid_forget()
            self.sidebar_visible = False
            
            self.btn_floating_back = ctk.CTkButton(
                self.viewer_frame,
                text="Sol Paneli Aç",
                width=110,
                height=30,
                command=self.toggle_fullscreen,
                fg_color="#10B981"
            )
            self.btn_floating_back.place(x=10, y=10)
        else:
            if hasattr(self, 'btn_floating_back'):
                self.btn_floating_back.destroy()
            self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            self.sidebar_visible = True
        
        self.root_after_id = self.after(50, self.render_page)

    def on_mousewheel(self, event):
        """Mouse tekerleğiyle dikey yönde pürüzsüz kaydırma sağlar."""
        try:
            if sys.platform == "win32":
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif sys.platform == "darwin":
                self.canvas.yview_scroll(int(-1 * event.delta), "units")
            else:
                if event.num == 4:
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(1, "units")
        except Exception:
            pass

    def change_theme(self, new_mode):
        if new_mode == "Sistem":
            ctk.set_appearance_mode("System")
        elif new_mode == "Koyu":
            ctk.set_appearance_mode("Dark")
        elif new_mode == "Açık":
            ctk.set_appearance_mode("Light")
        
        if self.doc:
            self.after(100, self.render_page)

if __name__ == "__main__":
    try:
        app = ModernPDFReader()
        app.mainloop()
    except Exception as e:
        # En nihai aşamada bile bir çökme olursa kullanıcıyı bilgilendir
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Kritik Hata", f"Program beklenmedik bir şekilde kapandı:\n{e}")