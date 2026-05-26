## ADDED Requirements

### Requirement: CLI starts a local Markdown web server
The system SHALL provide a CLI command that starts a web server for browsing and editing Markdown files under a selected root directory.

#### Scenario: Start from current directory
- **WHEN** the user runs the CLI without a root directory argument
- **THEN** the server uses the current working directory as the content root

#### Scenario: Start from explicit directory
- **WHEN** the user runs the CLI with an explicit root directory argument
- **THEN** the server uses that directory as the content root

#### Scenario: Missing root directory
- **WHEN** the user provides a root directory that does not exist
- **THEN** the CLI exits with a non-zero status and prints a clear error message

### Requirement: Server binds locally by default
The system SHALL bind to a local-only host by default and SHALL require explicit CLI configuration to listen on another host.

#### Scenario: Default host
- **WHEN** the user starts the server without a host option
- **THEN** the server listens on `127.0.0.1`

#### Scenario: Explicit host
- **WHEN** the user starts the server with a host option
- **THEN** the server listens on the requested host and prints the resulting URL

### Requirement: CLI reports server URL
The system SHALL print the browser URL after the server starts successfully.

#### Scenario: Successful startup
- **WHEN** the server is ready to accept requests
- **THEN** the CLI prints a URL containing the active host and port

### Requirement: Server uses default port with incremental fallback
The system SHALL use port `9026` by default and SHALL choose the next available port using `9026 + n` when the default port is occupied.

#### Scenario: Default port available
- **WHEN** the user starts the server without a port option and port `9026` is available
- **THEN** the server listens on port `9026`

#### Scenario: Default port occupied
- **WHEN** the user starts the server without a port option and port `9026` is occupied
- **THEN** the server tries port `9027`

#### Scenario: Multiple fallback ports occupied
- **WHEN** the user starts the server without a port option and ports `9026` through `9028` are occupied
- **THEN** the server tries port `9029`

#### Scenario: Explicit requested port unavailable
- **WHEN** the user starts the server with a specific port option and that port is already in use
- **THEN** the CLI exits with a non-zero status and explains that the requested port is unavailable

### Requirement: API paths stay inside the content root
The system SHALL reject any HTTP request that resolves to a file outside the selected content root.

#### Scenario: Path traversal attempt
- **WHEN** a request references `../` segments that would escape the content root
- **THEN** the server rejects the request without reading or writing the target path

#### Scenario: Absolute path attempt
- **WHEN** a request provides an absolute filesystem path outside the content root
- **THEN** the server rejects the request without reading or writing the target path
