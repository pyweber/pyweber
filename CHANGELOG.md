# PyWeber Changelog

## [1.0.0] - 2025-07-29
---
### Improvements
- Changed return if static template does not exist. Now, if static file not exist will be returned `Error Page Template`
- Added **hot reload for Python modules**. Now, changes to backend Python code automatically refresh the browser without restarting the server.

### Bug Fixes
- Solved NoneType Error when the route have no return middleware
- Solved not show title defined in route if route return Template instances.
- Solved multiple adding elements if use `e.update()` more than once.

## [0.9.98] - 2025-07-12
---
### New features
- Created loading screen, acessed adding `spinner` in Element's classes.

### Improvements
- Changed value type in `InputCheckBox` Element to Literal['on', 'off'] to str. `name` and `value` are now mandatory attribues for this Element.
- Changed pyweber official ico

## [0.9.97] - 2025-07-10
---
### New features
- **OpenAPI/Swagger Integration**: Full automatic OpenAPI 3.0 documentation generation with Swagger UI interface accessible at `/docs` endpoint
- **Multi-Type Model Support**: Automatic detection and processing of Pydantic models, dataclasses, and vanilla Python classes in route parameters
- **Smart Parameter Resolution**: Intelligent separation between path parameters and request body fields with automatic type inference
- **Dynamic Schema Generation**: Real-time OpenAPI schema creation based on function signatures and type annotations
- **Automatic Documentation**: Zero-configuration API documentation with interactive Swagger UI, including examples and validation schemas
- Added `files` attribute in `Element` instances. It is available only on `Input Elements` with type `file`
- Now you can get all files content loaded in real-time using event-handlers. Now, is not necessary post-request to get files
- Added `search_name_by_code` in HttpStatusCode instance. Now, you can get the http status_code description

### Technical Improvements
- **OpenApiProcessor Class**: New dedicated class for handling OpenAPI specification generation and type mapping
- **Enhanced Type System**: Comprehensive mapping between Python types and OpenAPI/JSON Schema types with format support
- **UUID-based Cache Busting**: Dynamic UUID generation for OpenAPI endpoint URLs to prevent caching issues
- **Flexible Model Instantiation**: Automatic object instantiation from request data regardless of model type (Pydantic, dataclass, or vanilla class)


## [0.9.96] - 2025-07-05
---
### Improvements

- Enhanced `<select>` and `<option>` support:
  - Fixed issue where `<option>` values were lost during server-client sync.
  - Options now preserve their `value` and `selected` states automatically without requiring manual `.value` assignment.
  - Defining `.value` on a `<select>` automatically sets the corresponding `<option>` as selected and removes `selected` from others.
  - `.value` getter on `<select>` returns the `value` of the selected `<option>`, or the first available one if none are explicitly selected.
  - Aligned with native HTML select behavior, reducing need for manual loops.

- Standardized `<textarea>` handling:
  - `.value` can now be used to both get and set values in `<textarea>`, while `.content` still works for initialization.
  - Calling `.value = "..."` on `<textarea>` also sets `.content`, ensuring two-way consistency.
  - `.value` getter returns `.content` for `<textarea>` elements.

- Cleaner task editing logic:
  - Editing forms now use direct `.value` assignments for `<select>`, `<textarea>`, and other fields — no longer requires iterating manually over options to apply `selected`.

- Backend-frontend synchronization improved:
  - Data reflection in inputs is now more consistent during updates and form submissions, especially when dynamically modifying templates.

### New features
- Added `Element.has_attr(name)`:
  - Utility method to check if a DOM element has a specific attribute.
  - Example usage: `if element.has_attr("selected")`.
  - Improves readability and encapsulates attribute logic more cleanly.

## [0.9.95] - 2025-07-04
---
### New features
- Allowed `ValueError` when create route with empty template value 
- Added `remove_before_middleware` and `remove_after_middleware` methods in MiddlewareManager instance do allow remove specific middleware.
- Added `behavior` parameter in scroll window methods. Now, you can choose one of options: `auto`, `smooth` or `instant`
- Changed return type from tuple to `MiddlewareResult` for process_middleware method in MiddlewareManager.
- Changed `childs` type for Element to `ChildElements` instances. Now you can use list methods e.g: `append`, `remove`, `extend`, `pop`, to manipulate childs without problem.

### Bug Fixes
- Fixed duplicate send events allways that target has document and window events. Now, window events only will be sent if it was created before.

## [0.9.94] - 2025-07-02
---
### New features
- Added `request` method in `Pyweber` to acess all request's methods in all program.
- Added `get_group_and_route` method in `Pyweber` to acess group and route on full route
- Added `sanitize` attribute an `sanitize_values` method to prevent XSS atack.
- Added `title` attribute in `Route` instances to define title in html templates if not exists.
- Added `raw_body` properity in Request instances for get brute bodies received from client-side
- Renamed `raw_request` to `raw_headers` to get headers received from client request
- Added `process_response` in Route instance to allow create or no the Template for all routes responses.
- Added the possibility to create a log file using Printline
- Improved terminal logs status now categorized into `INFO`, `ERROR` and `WARNING`

### Bug Fixes
- Fixed get correct selected value in `Select` Element
- Fixes get values checked in CheckBox and Radio Elements
- Fixed `TypeError` when try to replace variables in html
- Fixed `TypeError` when try to set attribute without value

## [0.9.93] - 2025-06-06
---
### Bug Fixes
- Fixed virtualdom error when trying to parse incompatible elements of the `div` and `tr` type
- Added the `data` parameter to the element
- Added return in the `pop_child` method of the Element

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