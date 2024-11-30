import sublime
import sublime_plugin
import os
import re
import threading

class CssIntellisense:
	css_classes = {}  # Dictionary untuk menyimpan kelas dan nama file
	sorted_completions = []  # Daftar kelas yang sudah diurutkan
	css_folders = []
	css_files = []
	enabled = True
	auto_search = False
	scopes = ["text.html", "text.html.php"]
	auto_refresh_interval = None

	@staticmethod
	def load_settings():
		settings = sublime.load_settings("CSS-Intellisense.sublime-settings")
		CssIntellisense.enabled = settings.get("enabled", True)
		CssIntellisense.scopes = settings.get("scopes", ["text.html", "text.html.php"])
		CssIntellisense.auto_search = settings.get("auto_search", True)
		CssIntellisense.auto_refresh_interval = settings.get("auto_refresh_interval", None)
		CssIntellisense.css_folders = settings.get("css_folders", [])
		CssIntellisense.css_files = settings.get("css_files", [])

	@staticmethod
	def update_sorted_completions():
		"""Update daftar autocomplete yang sudah diurutkan berdasarkan cache."""
		CssIntellisense.sorted_completions = sorted(
			[("{}\t{}".format(cls_name, file_name), cls_name)
			 for cls_name, file_name in CssIntellisense.css_classes.items()],
			key=lambda item: item[0]
		)

	@staticmethod
	def extract_classes(file_path):
		try:
			with open(file_path, 'r', encoding='utf-8') as file:
				content = file.read()
				classes = re.findall(r'\.([a-zA-Z0-9_-]+)', content)
				file_name = os.path.basename(file_path)
				
				for cls in classes:
					if cls not in CssIntellisense.css_classes:
						CssIntellisense.css_classes[cls] = file_name
		except Exception as e:
			print("Error reading {}: {}".format(file_path, e))

	@staticmethod
	def search_css_in_project():
		if CssIntellisense.auto_search:
			folders = sublime.active_window().folders()
			for folder in folders:
				CssIntellisense.add_css_folder(folder)

	@staticmethod
	def add_css_folder(folder_path):
		try:
			if folder_path not in CssIntellisense.css_folders:
				CssIntellisense.css_folders.append(folder_path)
			for root, dirs, files in os.walk(folder_path):
				for file in files:
					if file.endswith(".css"):
						file_path = os.path.join(root, file)
						CssIntellisense.extract_classes(file_path)
			CssIntellisense.update_sorted_completions()
			sublime.status_message("CSS Intellisense: Added CSS folder {}".format(folder_path))
		except Exception as e:
			print("Error adding CSS folder {}: {}".format(folder_path, e))

	@staticmethod
	def add_css_file(file_path):
		try:
			if file_path not in CssIntellisense.css_files:
				CssIntellisense.css_files.append(file_path)
			if file_path.endswith(".css"):
				CssIntellisense.extract_classes(file_path)
			CssIntellisense.update_sorted_completions()
			sublime.status_message("CSS Intellisense: Added CSS file {}".format(file_path))
		except Exception as e:
			print("Error adding CSS file {}: {}".format(file_path, e))

	@staticmethod
	def refresh_cache():
		CssIntellisense.css_classes.clear()
		for folder in CssIntellisense.css_folders:
			CssIntellisense.add_css_folder(folder)
		for file in CssIntellisense.css_files:
			CssIntellisense.add_css_file(file)
		CssIntellisense.update_sorted_completions()
		sublime.status_message("CSS Intellisense: Cache refreshed")

	@staticmethod
	def clear_cache():
		CssIntellisense.css_classes.clear()
		CssIntellisense.sorted_completions.clear()
		CssIntellisense.css_folders = []
		CssIntellisense.css_files = []
		sublime.status_message("CSS Intellisense: Cache cleared")

class AddCssFolderCommand(sublime_plugin.WindowCommand):
	def run(self, dirs):
		if dirs:
			folder_path = dirs[0]
			threading.Thread(target=CssIntellisense.add_css_folder, args=(folder_path,)).start()

class AddCssFileCommand(sublime_plugin.WindowCommand):
	def run(self, files):
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
		CssIntellisense.load_settings()
		if not CssIntellisense.enabled:
			return None
		
		for location in locations:
			if any(view.match_selector(location, scope) for scope in CssIntellisense.scopes):
				line_region = view.line(location)
				line_text = view.substr(line_region)

				matches = re.finditer(r'class="([^"]*)"', line_text)
				
				for match in matches:
					start, end = match.span(1)
					class_attr_start = line_region.begin() + start
					class_attr_end = line_region.begin() + end
					
					if class_attr_start <= location <= class_attr_end:
						# Gunakan sorted_completions langsung tanpa sorting ulang
						completions = [
							completion for completion in CssIntellisense.sorted_completions
							if prefix in completion[1]
						]
						return completions

		return None
