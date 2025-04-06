# PyWeber Changelog

## [0.8.4] - 2025-04-06
---
### Fixed
- Fixed `TypeError` when serializing HTML templates with comments ([#1](https://github.com/pyweber/pyweber/issues/1))

### New Features
- Added support for additional MIME types:
  - Office document formats (`doc`, `docx`, `xls`, `xlsx`, `pptx`, etc.)
  - Additional image formats (`bmp`, `webp`, `tif`, `tiff`)
- Introduced new `comment` Element tag for proper HTML comment handling
- Added support for dynamic templates with variable interpolation:
  - Template values can now be injected using `{{variable_name}}` syntax
  - Elements can be passed as template variables and will be properly rendered
  - Dynamic values can be provided via constructor kwargs
- Added environment variable `PYWEBER_RELOAD_MODE` to manage reload mode independently from configuration file

### Improvements
- Enhanced HTML parsing to properly handle and preserve comments
- Improved template rendering with more robust variable substitution
- Better error handling for malformed templates
- CLI now uses environment variables for reload mode, reducing dependency on configuration files


## [0.8.3] - 2025-04-05
---
### Fixed
- Fixed `FileNotFoundError` when try run on reload_mode if config file not exists

## [0.8.2] - 2025-04-05
---
### New Features
- Added comprehensive configuration management system
- Introduced interactive configuration editor via CLI
- Added support for custom configuration file paths and names
- Implemented `create-config-file` command for generating configuration files
- Added `add-section` command for managing configuration sections
- Enhanced project creation with `--with-config` flag
- Improved Window API with comprehensive browser interaction capabilities
- Added support for screen orientation detection and events

### Improvements
- Replaced Router with more powerful PyWeber class
- Enhanced CLI with more intuitive commands and options
- Improved hot reload functionality
- Added support for asynchronous event handlers
- Enhanced element manipulation API
- Improved error handling and reporting
- Updated documentation with comprehensive examples

### Fixed
- Fixed issues with WebSocket connections
- Resolved template rendering inconsistencies
- Fixed path handling in configuration system
- Addressed event propagation issues

## [0.8.1] - 2025-03-28
---

### New Features
- Added support for custom middleware
- Implemented session management
- Added cookie handling capabilities
- Introduced basic authentication helpers

### Improvements
- Enhanced routing system with parameter extraction
- Improved template rendering performance
- Added more DOM manipulation methods
- Enhanced event handling system

### Fixed
- Fixed static file serving issues
- Resolved template parsing errors
- Fixed WebSocket connection stability issues

## [0.8.0] - 2025-03-21
---

### New Features
- Initial release of PyWeber framework
- Implemented core Template system
- Added Element manipulation API
- Created event handling system
- Implemented basic routing
- Added WebSocket support for real-time updates
- Introduced hot reload for development
- Created CLI for project management

### Known Issues
- Limited middleware support
- Basic error handling
- Limited configuration options