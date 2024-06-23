import sublime
import sublime_plugin
import os
import re
import threading
import time

class CssIntellisense(sublime_plugin.EventListener):
    css_classes = {}
    css_folders = []
    css_files = []
    auto_search = False
    enabled = True
    auto_refresh_interval = False
    scopes = ["text.html"]

    @classmethod
    def refresh_cache(cls):
        if not cls.enabled:
            return
        cls.css_classes.clear()
        total_files = 0
        if cls.auto_search:
            cls.auto_search_css_files()
        total_files += len(cls.css_files)
        for folder in cls.css_folders:
            for root, _, files in os.walk(folder):
                total_files += len([file for file in files if file.endswith(".css")])
        current_file_count = 0
        window = sublime.active_window()
        if window:
            window.status_message("CSS Intellisense: Scanning files...")

        for folder in cls.css_folders:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith(".css"):
                        cls.extract_classes(os.path.join(root, file))
                        current_file_count += 1
                        progress = int((current_file_count / total_files) * 100)
                        window.status_message("CSS Intellisense: Scanning files... {}%".format(progress))
        for file in cls.css_files:
            cls.extract_classes(file)
            current_file_count += 1
            progress = int((current_file_count / total_files) * 100)
            window.status_message("CSS Intellisense: Scanning files... {}%".format(progress))
        
        window.status_message("CSS Intellisense: Scanning complete.")

    @classmethod
    def auto_search_css_files(cls):
        window = sublime.active_window()
        if window:
            folders = window.folders()
            for folder in folders:
                for root, _, files in os.walk(folder):
                    for file in files:
                        if file.endswith(".css"):
                            cls.css_files.append(os.path.join(root, file))

    @staticmethod
    def extract_classes(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                classes = re.findall(r'\.([a-zA-Z0-9_-]+)', content)
                file_name = os.path.basename(file_path)
                for cls in classes:
                    cls_key = (cls, file_name)
                    CssIntellisense.css_classes[cls_key] = cls_key
        except Exception as e:
            print("Error reading {}: {}".format(file_path, e))

    def on_query_completions(self, view, prefix, locations):
        if not self.enabled:
            return
        for scope in self.scopes:
            if view.match_selector(locations[0], scope):
                completions = [(cls_name + "\t" + file_name, cls_name) for (cls_name, file_name) in self.css_classes if prefix in cls_name]
                return completions

class AddCssFolderCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        CssIntellisense.css_folders.extend(dirs)
        CssIntellisense.refresh_cache()

class AddCssFileCommand(sublime_plugin.WindowCommand):
    def run(self, files):
        CssIntellisense.css_files.extend(files)
        CssIntellisense.refresh_cache()

class RefreshCssIntellisenseCommand(sublime_plugin.WindowCommand):
    def run(self):
        CssIntellisense.refresh_cache()
        sublime.message_dialog("CSS Intellisense cache refreshed!")

class ClearCssIntellisenseCacheCommand(sublime_plugin.WindowCommand):
    def run(self):
        CssIntellisense.css_classes.clear()
        sublime.message_dialog("CSS Intellisense cache cleared!")

class ToggleCssIntellisenseCommand(sublime_plugin.WindowCommand):
    def run(self, enable):
        CssIntellisense.enabled = enable
        if enable:
            CssIntellisense.refresh_cache()
        sublime.message_dialog("CSS Intellisense is now {}.".format("enabled" if enable else "disabled"))

def plugin_loaded():
    settings = sublime.load_settings("CSS-Intellisense.sublime-settings")
    CssIntellisense.css_folders = settings.get("css_folders", [])
    CssIntellisense.css_files = settings.get("css_files", [])
    CssIntellisense.auto_search = settings.get("auto_search", False)
    CssIntellisense.enabled = settings.get("enabled", True)
    CssIntellisense.auto_refresh_interval = settings.get("auto_refresh_interval", False)
    CssIntellisense.scopes = settings.get("scopes", ["text.html"])
    CssIntellisense.refresh_cache()
    
    if CssIntellisense.auto_refresh_interval and isinstance(CssIntellisense.auto_refresh_interval, int):
        threading.Thread(target=auto_refresh_cache, args=(CssIntellisense.auto_refresh_interval,)).start()

def auto_refresh_cache(interval):
    while True:
        if CssIntellisense.enabled:
            CssIntellisense.refresh_cache()
        time.sleep(interval)  # interval in seconds

def plugin_unloaded():
    settings = sublime.load_settings("CSS-Intellisense.sublime-settings")
    # settings.set("css_folders", CssIntellisense.css_folders)
    # settings.set("css_files", CssIntellisense.css_files)
    # settings.set("auto_search", CssIntellisense.auto_search)
    settings.set("enabled", CssIntellisense.enabled)
    # settings.set("auto_refresh_interval", CssIntellisense.auto_refresh_interval)
    # settings.set("scopes", CssIntellisense.scopes)
    sublime.save_settings("CSS-Intellisense.sublime-settings")
