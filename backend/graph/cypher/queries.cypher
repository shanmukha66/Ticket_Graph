// Graph RAG - Parameterized Cypher Queries
// These queries are loaded and executed from Python code

// ==============================================================================
// TICKET OPERATIONS
// ==============================================================================

// -- upsert_ticket --
// Upsert a Ticket node with all properties
// Parameters: id, project, priority, status, issueType, created, updated, summary, description, etc.
MERGE (t:Ticket {id: $id})
SET t.project = $project,
    t.priority = $priority,
    t.status = $status,
    t.issueType = $issueType,
    t.created = $created,
    t.updated = $updated,
    t.summary = $summary,
    t.description = $description,
    t.reporter = $reporter,
    t.assignee = $assignee
RETURN t;

// -- get_ticket --
// Fetch a single ticket by ID
// Parameters: id
MATCH (t:Ticket {id: $id})
RETURN t;

// -- get_tickets_by_project --
// Get all tickets for a project
// Parameters: project, limit
MATCH (t:Ticket {project: $project})
RETURN t
LIMIT $limit;


// ==============================================================================
// SECTION OPERATIONS
// ==============================================================================

// -- upsert_section --
// Upsert a Section node and attach to a Ticket
// Parameters: id, key, text, ticket_id
MATCH (t:Ticket {id: $ticket_id})
MERGE (s:Section {id: $id})
SET s.key = $key,
    s.text = $text
MERGE (t)-[:HAS_SECTION]->(s)
RETURN s;

// -- attach_section --
// Attach an existing section to a ticket
// Parameters: section_id, ticket_id
MATCH (t:Ticket {id: $ticket_id})
MATCH (s:Section {id: $section_id})
MERGE (t)-[:HAS_SECTION]->(s)
RETURN t, s;

// -- get_ticket_sections --
// Get all sections for a ticket
// Parameters: ticket_id
MATCH (t:Ticket {id: $ticket_id})-[:HAS_SECTION]->(s:Section)
RETURN s
ORDER BY s.key;


// ==============================================================================
// SIMILARITY EDGES
// ==============================================================================

// -- create_similarity_edge --
// Create a SIMILAR_TO relationship between tickets
// Parameters: from_id, to_id, score, method
MATCH (t1:Ticket {id: $from_id})
MATCH (t2:Ticket {id: $to_id})
MERGE (t1)-[r:SIMILAR_TO]->(t2)
SET r.score = $score,
    r.method = $method,
    r.created = datetime()
RETURN r;

// -- get_similar_tickets --
// Get tickets similar to a given ticket
// Parameters: ticket_id, min_score, limit
MATCH (t:Ticket {id: $ticket_id})-[r:SIMILAR_TO]->(similar:Ticket)
WHERE r.score >= $min_score
RETURN similar, r.score AS score
ORDER BY r.score DESC
LIMIT $limit;

// -- batch_create_similarities --
// Batch create multiple similarity edges
// Parameters: similarities (list of {from_id, to_id, score, method})
UNWIND $similarities AS sim
MATCH (t1:Ticket {id: sim.from_id})
MATCH (t2:Ticket {id: sim.to_id})
MERGE (t1)-[r:SIMILAR_TO]->(t2)
SET r.score = sim.score,
    r.method = sim.method,
    r.created = datetime()
RETURN count(r) AS created_count;


// ==============================================================================
// SUBGRAPH QUERIES
// ==============================================================================

// -- get_subgraph_1hop --
// Fetch 1-hop neighborhood around a set of tickets
// Parameters: ticket_ids (list)
MATCH (t:Ticket)
WHERE t.id IN $ticket_ids
OPTIONAL MATCH (t)-[r1:SIMILAR_TO|HAS_SECTION]-(n1)
RETURN t, r1, n1;

// -- get_subgraph_nhop --
// Fetch N-hop neighborhood around ticket(s)
// Parameters: ticket_ids (list), hops (int)
MATCH path = (t:Ticket)-[*1..$hops]-(n)
WHERE t.id IN $ticket_ids
RETURN path;

// -- get_subgraph_with_sections --
// Get tickets + sections + similarities in subgraph
// Parameters: ticket_ids (list)
MATCH (t:Ticket)
WHERE t.id IN $ticket_ids
OPTIONAL MATCH (t)-[:HAS_SECTION]->(s:Section)
OPTIONAL MATCH (t)-[sim:SIMILAR_TO]->(other:Ticket)
WHERE other.id IN $ticket_ids
RETURN t, collect(DISTINCT s) AS sections, collect(DISTINCT {ticket: other, score: sim.score}) AS similar;

// -- get_context_subgraph --
// Get full context: ticket + sections + similar tickets + their sections
// Parameters: ticket_id, similarity_threshold, max_similar
MATCH (t:Ticket {id: $ticket_id})
OPTIONAL MATCH (t)-[:HAS_SECTION]->(ts:Section)
OPTIONAL MATCH (t)-[sim:SIMILAR_TO]->(st:Ticket)
WHERE sim.score >= $similarity_threshold
WITH t, collect(DISTINCT ts) AS ticket_sections, 
     collect(DISTINCT {ticket: st, score: sim.score}) AS similar_tickets
     LIMIT $max_similar
UNWIND similar_tickets AS st_info
OPTIONAL MATCH (st_info.ticket)-[:HAS_SECTION]->(ss:Section)
RETURN t, 
       ticket_sections, 
       collect(DISTINCT {ticket: st_info.ticket, score: st_info.score, sections: collect(ss)}) AS similar_with_sections;


// ==============================================================================
// UTILITY QUERIES
// ==============================================================================

// -- count_nodes --
// Count all nodes by label
MATCH (n)
RETURN labels(n) AS label, count(n) AS count;

// -- count_relationships --
// Count all relationships by type
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(r) AS count;

// -- clear_similarities --
// Remove all SIMILAR_TO relationships
MATCH ()-[r:SIMILAR_TO]->()
DELETE r;

// -- delete_all --
// Clear entire graph (use with caution!)
MATCH (n)
DETACH DELETE n;

