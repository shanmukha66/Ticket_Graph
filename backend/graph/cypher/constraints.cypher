// Graph RAG - Database Constraints and Indexes
// Run these once to set up the schema

// ==============================================================================
// UNIQUENESS CONSTRAINTS
// ==============================================================================

// Ensure Ticket nodes have unique IDs
CREATE CONSTRAINT ticket_id_unique IF NOT EXISTS
FOR (t:Ticket) REQUIRE t.id IS UNIQUE;

// Ensure Section nodes have unique IDs
CREATE CONSTRAINT section_id_unique IF NOT EXISTS
FOR (s:Section) REQUIRE s.id IS UNIQUE;


// ==============================================================================
// INDEXES FOR QUERY PERFORMANCE
// ==============================================================================

// Index on Ticket properties for filtering
CREATE INDEX ticket_project IF NOT EXISTS
FOR (t:Ticket) ON (t.project);

CREATE INDEX ticket_issueType IF NOT EXISTS
FOR (t:Ticket) ON (t.issueType);

CREATE INDEX ticket_status IF NOT EXISTS
FOR (t:Ticket) ON (t.status);

// Index on Section key for lookups
CREATE INDEX section_key IF NOT EXISTS
FOR (s:Section) ON (s.key);

// Composite index for common query patterns
CREATE INDEX ticket_project_status IF NOT EXISTS
FOR (t:Ticket) ON (t.project, t.status);

// Optional: Full-text search indexes
// CREATE FULLTEXT INDEX ticket_text_search IF NOT EXISTS
// FOR (t:Ticket) ON EACH [t.summary, t.description];
//
// CREATE FULLTEXT INDEX section_text_search IF NOT EXISTS
// FOR (s:Section) ON EACH [s.text];

