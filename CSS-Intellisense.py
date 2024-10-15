import sublime
import sublime_plugin
import os
import re
import threading

class CssIntellisense:
    css_classes = {}
    css_folders = []
    css_files = []
    enabled = True
    auto_search = True
    scopes = ["text.html", "text.xml"]  # Sesuaikan dengan kebutuhan
    auto_refresh_interval = None  # Nilai default (None berarti tidak ada auto refresh)
    
    @staticmethod
    def load_settings():
        settings = sublime.load_settings("CSS-Intellisense.sublime-settings")
        CssIntellisense.enabled = settings.get("enabled", True)
        CssIntellisense.scopes = settings.get("scopes", ["text.html", "text.xml"])
        CssIntellisense.auto_search = settings.get("auto_search", True)
        CssIntellisense.auto_refresh_interval = settings.get("auto_refresh_interval", None)
        CssIntellisense.css_folders = settings.get("css_folders", [])
        CssIntellisense.css_files = settings.get("css_files", [])

    @staticmethod
    def extract_classes(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # Ambil daftar kelas dari file CSS
                classes = re.findall(r'\.([a-zA-Z0-9_-]+)', content)
                file_name = os.path.basename(file_path)
                
                for cls in classes:
                    # Tambahkan kelas hanya jika belum ada di cache
                    if cls not in CssIntellisense.css_classes:
                        CssIntellisense.css_classes[cls] = file_name
        except Exception as e:
            print("Error reading {}: {}".format(file_path, e))  # Print untuk Python 3.3

    @staticmethod
    def search_css_in_project():
        """Otomatis mencari file CSS di root project."""
        if CssIntellisense.auto_search:
            # Dapatkan root folder dari project
            folders = sublime.active_window().folders()
            for folder in folders:
                CssIntellisense.add_css_folder(folder)

    @staticmethod
    def add_css_folder(folder_path):
        try:
            # Tambahkan folder ke dalam daftar folder yang akan dipantau
            if folder_path not in CssIntellisense.css_folders:
                CssIntellisense.css_folders.append(folder_path)

            # Jangan reset atau kosongkan cache sebelumnya
            # Pastikan untuk hanya menambahkan hasil dari folder baru
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(".css"):
                        file_path = os.path.join(root, file)
                        CssIntellisense.extract_classes(file_path)
            
            # Setelah pemindaian, kirim pesan ke status bar
            sublime.status_message("CSS Intellisense: Added CSS folder {}".format(folder_path))
        
        except Exception as e:
            print("Error adding CSS folder {}: {}".format(folder_path, e))  # Print untuk Python 3.3

    @staticmethod
    def add_css_file(file_path):
        try:
            # Tambahkan file ke dalam daftar file yang akan dipantau
            if file_path not in CssIntellisense.css_files:
                CssIntellisense.css_files.append(file_path)

            # Pindai file CSS dan tambahkan ke cache, tanpa mereset cache sebelumnya
            if file_path.endswith(".css"):
                CssIntellisense.extract_classes(file_path)
            
            # Setelah pemindaian, kirim pesan ke status bar
            sublime.status_message("CSS Intellisense: Added CSS file {}".format(file_path))
        
        except Exception as e:
            print("Error adding CSS file {}: {}".format(file_path, e))  # Print untuk Python 3.3

    @staticmethod
    def refresh_cache():
        # Lakukan refresh terhadap cache CSS dengan cara memuat ulang semua file CSS
        CssIntellisense.css_classes.clear()

        # Proses pemindaian kembali untuk file dan folder yang diatur
        for folder in CssIntellisense.css_folders:
            CssIntellisense.add_css_folder(folder)

        for file in CssIntellisense.css_files:
            CssIntellisense.add_css_file(file)
        
        sublime.status_message("CSS Intellisense: Cache refreshed")

    @staticmethod
    def clear_cache():
        # Kosongkan cache sepenuhnya
        CssIntellisense.css_classes.clear()
        CssIntellisense.css_folders = []
        CssIntellisense.css_files = []
        sublime.status_message("CSS Intellisense: Cache cleared")

class AddCssFolderCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        # Mengambil folder dari klik kanan pada sidebar
        if dirs:
            folder_path = dirs[0]
            threading.Thread(target=CssIntellisense.add_css_folder, args=(folder_path,)).start()

class AddCssFileCommand(sublime_plugin.WindowCommand):
    def run(self, files):
        # Mengambil file dari klik kanan pada sidebar
        if files:
            file_path = files[0]
            threading.Thread(target=CssIntellisense.add_css_file, args=(file_path,)).start()

class RefreshCssCacheCommand(sublime_plugin.WindowCommand):
    def run(self):
        threading.Thread(target=CssIntellisense.refresh_cache).start()

class ClearCssCacheCommand(sublime_plugin.WindowCommand):
    def run(self):
        CssIntellisense.clear_cache()

class CssIntellisenseListener(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        CssIntellisense.load_settings()  # Pastikan settings terbaru di-load
        if not CssIntellisense.enabled:
            return None  # Plugin dinonaktifkan, tidak melakukan auto-complete
        
        # Cek apakah kursor berada di dalam atribut class=""
        for location in locations:
            # Ambil teks di sekitar kursor
            current_line = view.substr(view.line(location))
            
            # Cek apakah di sekitar kursor ada atribut class=""
            if 'class="' in current_line:
                # Cek apakah kursor berada di dalam nilai atribut class=""
                class_attr_start = current_line.find('class="') + len('class="')
                class_attr_end = current_line.find('"', class_attr_start)
                
                # Pastikan kursor berada di antara class=""
                if class_attr_start <= view.rowcol(location)[1] <= class_attr_end:
                    for scope in CssIntellisense.scopes:
                        # Cek apakah posisi kursor berada di dalam scope yang diizinkan
                        if view.match_selector(locations[0], scope):
                            # Buat daftar kelas untuk auto-complete dengan format yang benar
                            # Tambahkan pengurutan berdasarkan abjad
                            completions = sorted(
                                [("{}\t{}".format(cls_name, file_name), cls_name) 
                                 for cls_name, file_name in CssIntellisense.css_classes.items() 
                                 if prefix in cls_name],
                                key=lambda item: item[0]  # Urutkan berdasarkan nama kelas (item[0])
                            )
                            return completions

        return None  # Jika tidak ada yang cocok, return None
