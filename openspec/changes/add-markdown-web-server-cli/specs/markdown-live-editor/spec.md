## ADDED Requirements

### Requirement: Markdown file content can be opened
The system SHALL allow the browser UI to open a Markdown file from the index and retrieve its source content.

#### Scenario: Open indexed file
- **WHEN** the user selects an indexed Markdown file
- **THEN** the editor displays that file's Markdown source

#### Scenario: Open missing file
- **WHEN** the user selects a file that no longer exists
- **THEN** the UI displays a clear missing-file error and does not show stale content as current

### Requirement: Browser opens to Markdown index page
The system SHALL show a Markdown file index page when the local web server is opened in a browser.

#### Scenario: Initial browser load
- **WHEN** the user opens the server URL in a browser
- **THEN** the UI displays the indexed Markdown files from the content root

#### Scenario: Click indexed file
- **WHEN** the user clicks a Markdown file in the index
- **THEN** the UI opens that file in the editor and preview workspace

### Requirement: Browser UI uses Tailwind styling
The system SHALL use Tailwind CSS as the recommended styling library for the browser UI.

#### Scenario: UI assets loaded
- **WHEN** the user opens the server URL in a browser
- **THEN** the index and editor workspace use Tailwind-based layout and utility styling

### Requirement: Markdown preview renders HTML
The system SHALL render Markdown source into HTML for preview.

#### Scenario: Render heading and paragraph
- **WHEN** the selected Markdown contains a heading and paragraph
- **THEN** the preview displays corresponding rendered HTML elements

#### Scenario: Render fenced code block
- **WHEN** the selected Markdown contains a fenced code block that is not a supported diagram language
- **THEN** the preview displays it as a code block

### Requirement: Editing updates the preview live
The system SHALL update the rendered preview as the user edits Markdown source.

#### Scenario: User types in editor
- **WHEN** the user changes the Markdown source in the editor
- **THEN** the preview updates without a manual page refresh

### Requirement: Editor and preview use split panes
The system SHALL display Markdown source in a left pane and rendered HTML preview in a right pane when a file is open.

#### Scenario: File opened in split view
- **WHEN** the user opens an indexed Markdown file
- **THEN** the left pane displays editable Markdown source and the right pane displays rendered HTML

#### Scenario: Hide preview pane
- **WHEN** the user hides the right preview pane
- **THEN** the Markdown source pane remains visible and uses the available workspace

#### Scenario: Hide source pane
- **WHEN** the user hides the left source pane
- **THEN** the rendered HTML preview pane remains visible and uses the available workspace

#### Scenario: Restore both panes
- **WHEN** either pane is hidden and the user restores the split view
- **THEN** both source and preview panes are visible again

### Requirement: Pane width can be adjusted
The system SHALL allow the user to adjust the relative width of the Markdown source pane and rendered preview pane.

#### Scenario: Drag pane divider
- **WHEN** the user drags the divider between the source and preview panes
- **THEN** the UI updates the relative pane widths without reloading the selected file

#### Scenario: Minimum pane widths
- **WHEN** the user resizes panes
- **THEN** the UI enforces minimum usable widths so controls and text do not overlap

### Requirement: Edited Markdown can be saved
The system SHALL allow the user to save edited Markdown content back to the selected file.

#### Scenario: Save selected file
- **WHEN** the user saves changes to the selected Markdown file
- **THEN** the server writes the new content to that file under the content root

#### Scenario: Save outside root rejected
- **WHEN** a save request targets a path outside the content root
- **THEN** the server rejects the request without writing content

### Requirement: External file changes refresh the UI
The system SHALL notify the browser when Markdown files are added, removed, or changed on disk.

#### Scenario: New Markdown file added
- **WHEN** a Markdown file is added under the content root outside the browser UI
- **THEN** the index updates without requiring a full server restart

#### Scenario: Open file changed externally
- **WHEN** the selected Markdown file changes on disk outside the browser UI
- **THEN** the UI indicates that the file has changed and refreshes or offers a reload path
