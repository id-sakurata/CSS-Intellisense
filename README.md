# CSS-Intellisense

CSS Intellisense plugin for Sublime Text, providing auto-complete for CSS classes from specified files and folders.

## Features
- Auto-complete CSS classes from specified folders and files.
- Option to auto-search CSS files in the project root.
- Refresh cache manually or automatically.
- Add specific CSS files or folders via context menu.
- Configure scopes for auto-completion.

## Configuration
Edit the settings via `Preferences  Package Settings  CSS-Intellisense`.

```json
{
    css_folders [],
    css_files [],
    auto_search true,
    enabled true,
    auto_refresh_interval false,   Set to an integer value for seconds
    scopes [text.html]
}
```

## Usage
- Right-click on a folder or file in the sidebar to add it to the CSS auto-complete cache.
- Use the command palette to refresh or clear the cache.
- Enable or disable the plugin as needed.
