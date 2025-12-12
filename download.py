import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import re
import threading

# --- الثوابت ---
APP_ID = "1360490"
DEPOT_ID = "1360491"
MANIFEST_ID = "263468876206854407"
MANIFEST_FILE = ".\\PECO Manifests and Keys\\1360491_263468876206854407.manifest"
DEPOT_KEYS_FILE = ".\\PECO Manifests and Keys\\1360490.key"
DEPOT_DOWNLOADER_PATH = ".\\DepotDownloaderMod\\DepotDownloadermod.exe"
GAME_FOLDER_NAME = "PECO"

class GUIDownloaderApp:
    def __init__(self, master):
        self.master = master
        master.title("PECO Universal Game Download System")
        master.geometry("700x350") # تم زيادة الحجم لتناسب الخطوط الكبيرة
        
        # إعدادات إخفاء نافذة CMD
        if os.name == 'nt':
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.startupinfo.wShowWindow = subprocess.SW_HIDE
        else:
            self.startupinfo = None
        
        self.download_dir = tk.StringVar(master, value=os.path.join(os.getcwd(), GAME_FOLDER_NAME))
        self.current_status = tk.StringVar(master, value="الحالة: جاهز")
        self.download_info = tk.StringVar(master, value="0.0%") 

        self._setup_ui(master)

    def _setup_ui(self, master):
        # تعريف خط كبير لاستخدامه في العناوين والنسبة المئوية
        FONT_LARGE = ('Arial', 14, 'bold')
        FONT_PERCENTAGE = ('Courier', 24, 'bold')
        FONT_BUTTON = ('Arial', 16, 'bold')
        FONT_STATUS = ('Arial', 11)

        main_frame = tk.Frame(master, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # واجهة اختيار المجلد
        tk.Label(main_frame, text="مسار التنزيل:", font=FONT_LARGE).pack(anchor=tk.W, pady=(5, 0))
        dir_frame = tk.Frame(main_frame)
        dir_frame.pack(fill=tk.X, pady=5)
        self.dir_entry = tk.Entry(dir_frame, textvariable=self.download_dir, width=50, state='readonly', font=FONT_STATUS)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        select_btn = tk.Button(dir_frame, text="اختيار مجلد", command=self.select_folder, font=FONT_STATUS)
        select_btn.pack(side=tk.RIGHT)

        # شريط التقدم
        tk.Label(main_frame, text="تقدم التحميل:", font=FONT_LARGE).pack(anchor=tk.W, pady=(15, 5))
        self.progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=500, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # معلومات التحميل (النسبة المئوية فقط - بخط كبير جداً)
        tk.Label(main_frame, textvariable=self.download_info, font=FONT_PERCENTAGE, fg='blue').pack(pady=10)

        # زر بدء التحميل
        self.download_btn = tk.Button(main_frame, text="بدء التحميل", command=self.start_download, bg='#4CAF50', fg='white', font=FONT_BUTTON, height=2)
        self.download_btn.pack(pady=20, fill=tk.X)
        
        # شريط الحالة في الأسفل (لعرض رسائل البرنامج النصية)
        self.status_label = tk.Label(master, textvariable=self.current_status, bd=1, relief=tk.SUNKEN, anchor=tk.W, font=FONT_STATUS)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

    def select_folder(self):
        initial_dir = os.path.dirname(self.download_dir.get()) if os.path.exists(os.path.dirname(self.download_dir.get())) else os.getcwd()
        folder_selected = filedialog.askdirectory(initialdir=initial_dir, title="يرجى اختيار مجلد التنزيل")
        if folder_selected:
            final_path = os.path.join(folder_selected, GAME_FOLDER_NAME)
            self.download_dir.set(final_path)

    def update_progress(self, progress, status_msg):
        """لتحديث شريط التقدم ورسالة الحالة."""
        self.progress_bar['value'] = progress
        self.download_info.set(f"{progress:.1f}%") # النسبة المئوية
        self.current_status.set(f"الحالة: {status_msg}") # رسالة حالة البرنامج
        self.master.update()

    def start_download(self):
        self.download_btn.config(state='disabled', text="جاري التحميل...")
        self.current_status.set("الحالة: بدأ التحميل...")
        self.update_progress(0, "بدء عملية التحميل...")
        
        download_thread = threading.Thread(target=self._run_depot_downloader)
        download_thread.start()

    def _get_status_label(self, stripped_line):
        """يحدد رسالة الحالة باللغة العربية مع إبقاء الكلمة المفتاحية الإنجليزية."""
        lower_line = stripped_line.lower()
        
        if "downloading" in lower_line or "download" in lower_line:
            return f"جاري التحميل... ({stripped_line})"
        elif "verifying" in lower_line or "verify" in lower_line or "checking" in lower_line:
            return f"جاري التحقق من الملفات... ({stripped_line})"
        elif "finished" in lower_line or "complete" in lower_line:
            return "اكتمل."
        
        # إذا كان سطر التقدم، نعرضه كما هو
        return stripped_line

    def _run_depot_downloader(self):
        download_path = self.download_dir.get()
        os.makedirs(download_path, exist_ok=True)
        self.current_status.set(f"الحالة: جاري التنزيل إلى: {download_path}")

        command = [
            DEPOT_DOWNLOADER_PATH,
            "-app", APP_ID,
            "-depot", DEPOT_ID,
            "-manifest", MANIFEST_ID,
            "-manifestfile", MANIFEST_FILE,
            "-depotkeys", DEPOT_KEYS_FILE,
            "-dir", download_path,
            "-max-downloads", "256",
            "-verify-all"
        ]

        # النمط البسيط للبحث عن النسبة المئوية
        simple_progress_pattern = re.compile(r"(\d+\.?\d*)\s*%")
        
        last_progress = 0.0

        try:
            # تشغيل العملية الفرعية مع إخفاء نافذة الـ CMD
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                startupinfo=self.startupinfo,
                bufsize=1, 
                universal_newlines=True
            )

            # قراءة المخرجات خطاً بخط
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    stripped_line = line.strip()
                    progress = None
                    
                    # 1. تحديد رسالة الحالة
                    status_message = self._get_status_label(stripped_line)
                    
                    # 2. محاولة استخراج النسبة المئوية (لتحريك البار)
                    match_simple = simple_progress_pattern.search(stripped_line)
                    
                    if match_simple:
                        try:
                            # النسبة المئوية
                            progress = float(match_simple.group(1))
                            last_progress = progress
                        except ValueError:
                            pass

                    # تحديث الواجهة باستخدام آخر نسبة مئوية ورسالة الحالة الحالية
                    self.update_progress(last_progress, status_message)


                    # البحث عن رسالة الانتهاء
                    if "Download finished successfully." in stripped_line:
                         self.current_status.set("الحالة: اكتمل التحميل بنجاح...")


            process.wait()

            if process.returncode == 0:
                self.current_status.set("الحالة: اكتمل التحميل بنجاح!")
                self.update_progress(100.0, "اكتمل التحميل.")
                messagebox.showinfo("اكتمل", "تم الانتهاء من التحميل بنجاح.")
            else:
                self.current_status.set(f"الحالة: فشل التحميل (رمز الخروج: {process.returncode})")
                messagebox.showerror("فشل", "فشل التحميل.")
                
        except Exception as e:
            self.current_status.set(f"الحالة: خطأ غير متوقع: {e}")
            messagebox.showerror("خطأ", f"حدث خطأ: {e}")

        finally:
            self.download_btn.config(state='normal', text="بدء التحميل")


if __name__ == "__main__":
    root = tk.Tk()
    app = GUIDownloaderApp(root)
    root.mainloop()