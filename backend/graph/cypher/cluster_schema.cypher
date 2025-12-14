// ============================================================================
// NEO4J SCHEMA FOR SUPPORT TICKET CLUSTERING SYSTEM
// ============================================================================
//
// Schema Design:
// - (:Ticket) nodes with embeddings stored as vector property
// - (:Cluster) nodes with type and granularity level
// - (:Ticket)-[:BELONGS_TO]->(:Cluster) relationships
//
// ============================================================================

// ----------------------------------------------------------------------------
// CONSTRAINTS AND INDEXES
// ----------------------------------------------------------------------------

// Unique constraint on Ticket ID
CREATE CONSTRAINT ticket_id_unique IF NOT EXISTS
FOR (t:Ticket) REQUIRE t.id IS UNIQUE;

// Unique constraint on Cluster ID
CREATE CONSTRAINT cluster_id_unique IF NOT EXISTS
FOR (c:Cluster) REQUIRE c.id IS UNIQUE;

// Index on Ticket category for filtering
CREATE INDEX ticket_category IF NOT EXISTS
FOR (t:Ticket) ON (t.category);

// Index on Ticket priority for filtering
CREATE INDEX ticket_priority IF NOT EXISTS
FOR (t:Ticket) ON (t.priority);

// Index on Ticket status for filtering
CREATE INDEX ticket_status IF NOT EXISTS
FOR (t:Ticket) ON (t.status);

// Index on Ticket created_at for time-based queries
CREATE INDEX ticket_created_at IF NOT EXISTS
FOR (t:Ticket) ON (t.created_at);

// Index on Cluster type for filtering
CREATE INDEX cluster_type IF NOT EXISTS
FOR (c:Cluster) ON (c.type);

// Index on Cluster granularity_level for filtering
CREATE INDEX cluster_granularity IF NOT EXISTS
FOR (c:Cluster) ON (c.granularity_level);

// Composite index for cluster lookups
CREATE INDEX cluster_type_granularity IF NOT EXISTS
FOR (c:Cluster) ON (c.type, c.granularity_level);

// ============================================================================
// EXAMPLE QUERIES
// ============================================================================

// ----------------------------------------------------------------------------
// 1. CREATE TICKET NODES
// ----------------------------------------------------------------------------

// Single ticket creation
CREATE (t:Ticket {
  id: 'TICKET-10000',
  title: 'Cannot login with email',
  description: 'User cannot login using registered email address. Error: Invalid credentials',
  category: 'login issue',
  priority: 'high',
  status: 'open',
  created_at: '2024-10-15T14:30:00',
  embedding_vector: [0.123, -0.456, 0.789, ...]  // 768-dimensional vector
})
RETURN t;

// Batch ticket creation
UNWIND $tickets AS ticket
CREATE (t:Ticket {
  id: ticket.id,
  title: ticket.title,
  description: ticket.description,
  category: ticket.category,
  priority: ticket.priority,
  status: ticket.status,
  created_at: ticket.created_at,
  embedding_vector: ticket.embedding_vector
})
RETURN count(t) AS tickets_created;

// ----------------------------------------------------------------------------
// 2. STORE EMBEDDINGS
// ----------------------------------------------------------------------------

// Option A: Embedding as vector property (recommended for Neo4j 5.x+)
// Embeddings are stored directly in the Ticket node
MATCH (t:Ticket {id: 'TICKET-10000'})
SET t.embedding_vector = $embedding_vector
RETURN t;

// Batch update embeddings
UNWIND $embeddings AS embedding_data
MATCH (t:Ticket {id: embedding_data.ticket_id})
SET t.embedding_vector = embedding_data.vector
RETURN count(t) AS embeddings_updated;

// Option B: Embedding as separate node (alternative approach)
// Create embedding nodes and link to tickets
MATCH (t:Ticket {id: 'TICKET-10000'})
CREATE (e:Embedding {
  id: 'EMB-' + t.id,
  vector: $embedding_vector,
  dimension: 768,
  model: 'e5-base-v2'
})
CREATE (t)-[:HAS_EMBEDDING]->(e)
RETURN e;

// ----------------------------------------------------------------------------
// 3. CREATE CLUSTER NODES
// ----------------------------------------------------------------------------

// Single cluster creation
CREATE (c:Cluster {
  id: 'A_cluster_0',
  type: 'A',                    // Cluster type: A (coarse), B (medium), C (fine)
  label: 'Authentication Issues',
  granularity_level: 'coarse',   // coarse, medium, or fine
  ticket_count: 1000,
  dominant_category: 'login issue',
  centroid: [0.123, -0.456, ...] // Cluster centroid vector
})
RETURN c;

// Batch cluster creation
UNWIND $clusters AS cluster_data
CREATE (c:Cluster {
  id: cluster_data.id,
  type: cluster_data.type,
  label: cluster_data.label,
  granularity_level: cluster_data.granularity_level,
  ticket_count: cluster_data.ticket_count,
  dominant_category: cluster_data.dominant_category,
  centroid: cluster_data.centroid
})
RETURN count(c) AS clusters_created;

// ----------------------------------------------------------------------------
// 4. LINK TICKETS TO CLUSTERS
// ----------------------------------------------------------------------------

// Single relationship creation
MATCH (t:Ticket {id: 'TICKET-10000'})
MATCH (c:Cluster {id: 'A_cluster_0'})
CREATE (t)-[:BELONGS_TO {
  cluster_type: 'A',
  assigned_at: datetime(),
  similarity_score: 0.85
}]->(c)
RETURN t, c;

// Batch relationship creation
UNWIND $assignments AS assignment
MATCH (t:Ticket {id: assignment.ticket_id})
MATCH (c:Cluster {id: assignment.cluster_id})
CREATE (t)-[:BELONGS_TO {
  cluster_type: assignment.cluster_type,
  assigned_at: datetime(),
  similarity_score: assignment.similarity_score
}]->(c)
RETURN count(*) AS relationships_created;

// ----------------------------------------------------------------------------
// 5. QUERY EXAMPLES
// ----------------------------------------------------------------------------

// Get all tickets in a cluster
MATCH (c:Cluster {id: 'A_cluster_0'})<-[:BELONGS_TO]-(t:Ticket)
RETURN c, collect(t) AS tickets
LIMIT 100;

// Get all clusters for a ticket
MATCH (t:Ticket {id: 'TICKET-10000'})-[:BELONGS_TO]->(c:Cluster)
RETURN t, collect(c) AS clusters;

// Find similar tickets using embedding similarity
// Note: This requires vector similarity functions (Neo4j GDS or custom)
MATCH (t1:Ticket {id: 'TICKET-10000'})
MATCH (t2:Ticket)
WHERE t1 <> t2 AND t1.embedding_vector IS NOT NULL AND t2.embedding_vector IS NOT NULL
WITH t1, t2,
     gds.similarity.cosine(t1.embedding_vector, t2.embedding_vector) AS similarity
WHERE similarity > 0.7
RETURN t2.id, t2.title, similarity
ORDER BY similarity DESC
LIMIT 10;

// Get tickets by cluster type
MATCH (t:Ticket)-[:BELONGS_TO {cluster_type: 'A'}]->(c:Cluster)
WHERE c.type = 'A'
RETURN c.id AS cluster_id, c.label AS cluster_label, 
       collect(t.id) AS ticket_ids, count(t) AS ticket_count
ORDER BY ticket_count DESC;

// Get cluster statistics
MATCH (c:Cluster)
RETURN c.type AS cluster_type,
       c.granularity_level AS granularity,
       count(c) AS num_clusters,
       avg(c.ticket_count) AS avg_tickets_per_cluster,
       min(c.ticket_count) AS min_tickets,
       max(c.ticket_count) AS max_tickets
ORDER BY c.type;

// Find tickets by category and cluster
MATCH (t:Ticket {category: 'login issue'})-[:BELONGS_TO]->(c:Cluster {type: 'B'})
RETURN c.id AS cluster_id, c.label AS cluster_label,
       collect(t.id) AS ticket_ids,
       count(t) AS ticket_count
ORDER BY ticket_count DESC;

// Get tickets with their cluster assignments
MATCH (t:Ticket)
OPTIONAL MATCH (t)-[r:BELONGS_TO]->(c:Cluster)
RETURN t.id AS ticket_id,
       t.title AS title,
       t.category AS category,
       t.status AS status,
       collect({
         cluster_id: c.id,
         cluster_type: c.type,
         cluster_label: c.label,
         similarity: r.similarity_score
       }) AS clusters
LIMIT 20;

// ----------------------------------------------------------------------------
// 6. MAINTENANCE QUERIES
// ----------------------------------------------------------------------------

// Update cluster ticket count
MATCH (c:Cluster {id: 'A_cluster_0'})
WITH c, size([(c)<-[:BELONGS_TO]-(t:Ticket) | t]) AS actual_count
SET c.ticket_count = actual_count
RETURN c.id, c.ticket_count;

// Recalculate all cluster ticket counts
MATCH (c:Cluster)
WITH c, size([(c)<-[:BELONGS_TO]-(t:Ticket) | t]) AS actual_count
SET c.ticket_count = actual_count
RETURN c.type, count(c) AS clusters_updated;

// Find tickets without embeddings
MATCH (t:Ticket)
WHERE t.embedding_vector IS NULL
RETURN t.id, t.title
LIMIT 100;

// Find clusters without tickets
MATCH (c:Cluster)
WHERE NOT EXISTS((c)<-[:BELONGS_TO]-())
RETURN c.id, c.type, c.label;

// Delete orphaned relationships
MATCH (t:Ticket)-[r:BELONGS_TO]->(c:Cluster)
WHERE NOT EXISTS((t)-[:BELONGS_TO]->(c))
DELETE r;

// ============================================================================
// VECTOR SIMILARITY SEARCH (Neo4j GDS or Custom Implementation)
// ============================================================================

// Note: Neo4j doesn't have built-in vector similarity search.
// You can use:
// 1. Neo4j GDS library functions (if available)
// 2. Custom Cypher with cosine similarity calculation
// 3. External vector database (FAISS) for similarity search

// Example: Cosine similarity calculation in Cypher
// (This is computationally expensive for large datasets)
MATCH (t1:Ticket {id: $query_ticket_id})
MATCH (t2:Ticket)
WHERE t1 <> t2 
  AND t1.embedding_vector IS NOT NULL 
  AND t2.embedding_vector IS NOT NULL
WITH t1, t2,
     reduce(s = 0.0, i IN range(0, size(t1.embedding_vector)-1) | 
       s + t1.embedding_vector[i] * t2.embedding_vector[i]
     ) AS dot_product,
     sqrt(reduce(s = 0.0, x IN t1.embedding_vector | s + x^2)) AS norm1,
     sqrt(reduce(s = 0.0, x IN t2.embedding_vector | s + x^2)) AS norm2
WITH t1, t2, dot_product / (norm1 * norm2) AS cosine_similarity
WHERE cosine_similarity > 0.7
RETURN t2.id, t2.title, cosine_similarity
ORDER BY cosine_similarity DESC
LIMIT 10;

// ============================================================================
// CLEANUP (Use with caution!)
// ============================================================================

// Delete all tickets and clusters
// MATCH (n)
// DETACH DELETE n;

// Delete only tickets
// MATCH (t:Ticket)
// DETACH DELETE t;

// Delete only clusters
// MATCH (c:Cluster)
// DETACH DELETE c;

// Delete relationships only
// MATCH ()-[r:BELONGS_TO]->()
// DELETE r;



