# PyWeber Changelog

## [0.9.92] - 2025-05-29
---
### Bug Fixes
- Fixed request validation method using https methods
- Fixed error when accessing static files

## [0.9.90] - 2025-05-24
---
### Bug Fixes
- Fixed error when serializing form data to form data dict using
- Fixed error when trying to redirect dynamic routes.
- Fixed error with `value` attribute of Elements that have events defined

## [0.9.7] - 2025-04-19
---
### New Features
- Implemented TemplateDiff system for efficient DOM updates:
  - Added intelligent diffing algorithm to detect exact changes between templates
  - Implemented efficient client-side patching to apply only necessary DOM updates
  - Reduced network traffic by sending only changed elements instead of full templates
- Added comprehensive deep cloning system for Element and Template objects:
  - Introduced `.clone` property for creating independent copies with preserved structure
  - Implemented support for cloning of nested elements with proper parent references
- Added component-based architecture with new HTML form elements:
  - Introduced `InputText`, `InputPassword`, `InputNumber`, `InputFile`, and other form components
  - Added comprehensive `TextArea` component with proper event handling
  - Implemented proper attribute management for all form components
- Enhanced WebSocket communication with optimized payload structure

### Improvements
- Optimized template rendering pipeline for better performance
- Improved event handling system with better event targeting
- Enhanced session management system for multiple browser tabs
- Refined UUID-based element tracking for more precise DOM manipulation
- Updated client-side JavaScript for efficient template diff application

### Bug Fixes
- Fix `pyweber run` and `pyweber -r` commands to run pyweber projects in linux system
- Fixed event handling for dynamically created elements
- Resolved issues with component attribute inheritance

## [0.9.6] - 2025-04-14
---
### Bug Fixes
- Resolved a `FileNotFoundError` that occurred when loading static files on Linux systems.

### New Features
- Added support for managing both `LocalStorage` and `SessionStorage`.
I- ntroduced support for native browser window methods such as `alert`, `prompt`, `confirm`, `atob`, `btoa`, `open`, `close`, and `scroll events`.
- Implemented a non-blocking system for handling both synchronous and asynchronous events, ensuring the main thread remains responsive.
- Server configuration can now be set directly in the run method. Parameters such as `ws_port`, `host`, `port`, key_file, and `cert_file` can be passed using `**kwargs` via `app.run()` or `pw.run()`.

### Improvements
- The window object is now globally accessible through the main module via `pw.window`.
- Removed window access from the app object — it is no longer available via `app.window`.

## [0.9.4] - 2025-04-08
---
### Bug Fixes
- Fixed `SyntaxError` when format f-string in non-windows systems

## [0.9.3] - 2025-04-08
---
### New Features
- Added `Icon Element` as pre-builded Elements called `Components`
- Added Bootstrap Icons. You need to import before on html or css to use it.
- Added Uvicorn and Gunicorn servers.

## [0.9.2] - 2025-04-07
---
### Bug Fixes
- Fixed the non-updating of values ​​when creating the config file

## [0.9.1] - 2025-04-07
---
### New Features
- Added `set_header()` method to Response class for modifying existing headers
- Added `add_header()` method to Response class for adding new headers
- Added support for asynchronous `after_request` middleware
- Improved HTML rendering with conditional DOCTYPE handling:
  - DOCTYPE is now only added when the root element is `<html>`
  - Fixed nested template rendering issues

### Improvements
- Enhanced Response class with better header management
- Optimized template rendering for dynamic content
- Better error handling and logging for HTTP responses
- Improved middleware processing with support for both synchronous and asynchronous functions
- Fixed reload mode detection to properly handle string environment variables:
  - Now correctly recognizes 'True', '1', True, and 1 as valid values
  - Ensures consistent behavior when setting reload mode via environment variables

### Bug Fixes
- Fixed issue with duplicate DOCTYPE declarations in nested templates
- Fixed middleware processing to properly handle both Request and Response objects
- Corrected HTTP version handling in Response headers
- Fixed content length calculation when response content is modified
- Resolved inconsistency in reload mode activation when set via environment variables

### Documentation
- Updated Response class documentation with new methods
- Added examples for asynchronous middleware usage
- Improved template rendering documentation

### Internal Changes
- Refactored Response class for better maintainability
- Improved type annotations throughout the codebase
- Enhanced middleware processing pipeline
- Added proper timezone handling for HTTP Date headers

## [0.9.0] - 2025-04-07
---
### New Features
- Added HTTPS/SSL support for secure connections:
  - Implemented SSL context configuration for HTTP server
  - Added WSS (WebSocket Secure) support for real-time connections
  - Support for custom certificates and self-signed certificates
  - Auto-generation of development certificates
- Added configuration options for SSL in both HTTP and WebSocket servers
- Improved CLI with SSL configuration options
- Added comprehensive environment variables support:
  - `PYWEBER_RELOAD_MODE` for controlling hot reload
  - `PYWEBER_HTTPS_ENABLED` for enabling/disabling HTTPS
  - `PYWEBER_CERT_FILE` and `PYWEBER_KEY_FILE` for SSL certificates
  - `PYWEBER_SERVER_HOST` and `PYWEBER_SERVER_PORT` for server configuration
  - `PYWEBER_WS_PORT` for WebSocket server port

### Improvements
- Enhanced security with proper SSL implementation
- Better error handling for SSL-related issues
- Improved WebSocket connection stability over secure connections
- Added detailed logging for connection issues
- Environment variables now take precedence over configuration files
- Added new CLI commands for certificate management:
  - `cert check-mkcert` to verify mkcert installation
  - `cert mkcert` to generate locally-trusted certificates
- Enhanced `run` command with additional server configuration options

### Documentation
- Added new documentation for environment variables
- Updated SSL/HTTPS setup guides
- Added certificate management instructions

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