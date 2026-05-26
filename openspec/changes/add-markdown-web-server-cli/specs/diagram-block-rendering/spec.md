## ADDED Requirements

### Requirement: Mermaid blocks render as diagrams
The system SHALL render fenced Markdown code blocks marked as `mermaid` into visual diagrams in the preview.

#### Scenario: Valid Mermaid block
- **WHEN** the Markdown contains a valid fenced `mermaid` block
- **THEN** the preview displays the rendered Mermaid diagram instead of raw Mermaid text

#### Scenario: Invalid Mermaid block
- **WHEN** the Markdown contains an invalid fenced `mermaid` block
- **THEN** the preview displays a visible diagram error for that block without breaking the rest of the document

### Requirement: PlantUML blocks render as images
The system SHALL render fenced Markdown code blocks marked as `plantuml` or `puml` into visual diagram images in the preview.

#### Scenario: Valid PlantUML block
- **WHEN** the Markdown contains a valid fenced `plantuml` block and a PlantUML renderer is available
- **THEN** the preview displays the rendered PlantUML diagram as an image or SVG

#### Scenario: PlantUML renderer unavailable
- **WHEN** the Markdown contains a fenced `plantuml` block and no PlantUML renderer is available
- **THEN** the preview displays a visible renderer-unavailable message for that block

#### Scenario: Invalid PlantUML block
- **WHEN** the Markdown contains an invalid fenced `plantuml` block
- **THEN** the preview displays a visible diagram error for that block without breaking the rest of the document

### Requirement: Diagram source remains editable Markdown
The system SHALL preserve the original Mermaid and PlantUML source text in the Markdown editor.

#### Scenario: Edit diagram source
- **WHEN** the user edits a Mermaid or PlantUML fenced block in the Markdown editor
- **THEN** the editor keeps the fenced block as Markdown source and the preview re-renders the diagram

### Requirement: Diagram rendering is isolated per block
The system SHALL isolate diagram rendering so that one failed diagram does not prevent other diagrams or Markdown content from rendering.

#### Scenario: Mixed valid and invalid diagrams
- **WHEN** the Markdown contains one valid diagram block and one invalid diagram block
- **THEN** the preview displays the valid diagram and a separate error for the invalid diagram
