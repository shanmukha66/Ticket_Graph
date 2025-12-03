// ============================================================================
// NEO4J QUERIES FOR CLUSTERING DEMO
// ============================================================================
// These queries help you explore and visualize clustering results in Neo4j
// for all 9 combinations: A/B/C (100/500/1000) × K-Means/Agglomerative/DBSCAN
// ============================================================================

// ----------------------------------------------------------------------------
// 1. GET TICKETS WITH EMBEDDINGS (for clustering)
// ----------------------------------------------------------------------------

// Get all tickets with embeddings (for query-based clustering)
MATCH (t:Ticket)
WHERE t.embedding_vector IS NOT NULL
RETURN t.id AS ticket_id,
       t.title AS title,
       t.description AS description,
       t.category AS category,
       t.priority AS priority,
       t.status AS status,
       t.created_at AS created_at,
       size(t.embedding_vector) AS embedding_dimension
LIMIT 1000;

// Get top 100 tickets (for A: 100 tickets clustering)
MATCH (t:Ticket)
WHERE t.embedding_vector IS NOT NULL
WITH t, rand() AS r
ORDER BY r
RETURN t.id AS ticket_id,
       t.title AS title,
       t.category AS category
LIMIT 100;

// Get top 500 tickets (for B: 500 tickets clustering)
MATCH (t:Ticket)
WHERE t.embedding_vector IS NOT NULL
WITH t, rand() AS r
ORDER BY r
RETURN t.id AS ticket_id,
       t.title AS title,
       t.category AS category
LIMIT 500;

// Get top 1000 tickets (for C: 1000 tickets clustering)
MATCH (t:Ticket)
WHERE t.embedding_vector IS NOT NULL
WITH t, rand() AS r
ORDER BY r
RETURN t.id AS ticket_id,
       t.title AS title,
       t.category AS category
LIMIT 1000;

// ----------------------------------------------------------------------------
// 2. QUERY-BASED TICKET RETRIEVAL (vector similarity search)
// ----------------------------------------------------------------------------

// Note: This requires computing query embedding first, then comparing
// For now, this shows the structure - you'll need to compute similarity in Python/backend

// Get tickets similar to a query (pseudo-code structure)
// MATCH (t:Ticket)
// WHERE t.embedding_vector IS NOT NULL
// WITH t, 
//      cosineSimilarity(t.embedding_vector, $query_embedding) AS similarity
// WHERE similarity > 0.5
// RETURN t.id, t.title, similarity
// ORDER BY similarity DESC
// LIMIT 1000;

// ----------------------------------------------------------------------------
// 3. CLUSTER NODES (if clusters are stored in Neo4j)
// ----------------------------------------------------------------------------

// NOTE: Cluster nodes don't have an "algorithm" property stored in Neo4j
// The algorithm is determined by the cluster type:
// - Type A = K-Means (100 tickets per cluster)
// - Type B = DBSCAN (500 tickets per cluster)  
// - Type C = Agglomerative (1000 tickets per cluster)

// Get all clusters of type A (100 tickets, K-Means)
MATCH (c:Cluster {type: 'A'})
RETURN c.id AS cluster_id,
       c.label AS label,
       c.ticket_count AS ticket_count,
       c.granularity_level AS granularity,
       c.dominant_category AS dominant_category,
       'K-Means' AS algorithm
ORDER BY c.ticket_count DESC;

// Get all clusters of type B (500 tickets, DBSCAN)
MATCH (c:Cluster {type: 'B'})
RETURN c.id AS cluster_id,
       c.label AS label,
       c.ticket_count AS ticket_count,
       c.granularity_level AS granularity,
       c.dominant_category AS dominant_category,
       'DBSCAN' AS algorithm
ORDER BY c.ticket_count DESC;

// Get all clusters of type C (1000 tickets, Agglomerative)
MATCH (c:Cluster {type: 'C'})
RETURN c.id AS cluster_id,
       c.label AS label,
       c.ticket_count AS ticket_count,
       c.granularity_level AS granularity,
       c.dominant_category AS dominant_category,
       'Agglomerative Clustering' AS algorithm
ORDER BY c.ticket_count DESC;

// ----------------------------------------------------------------------------
// 4. TICKETS IN CLUSTERS (if BELONGS_TO relationships exist)
// ----------------------------------------------------------------------------

// Get tickets in Cluster A (K-Means, 100 tickets per cluster)
MATCH (t:Ticket)-[r:BELONGS_TO]->(c:Cluster {type: 'A'})
RETURN c.id AS cluster_id,
       c.label AS cluster_label,
       collect(t.id) AS ticket_ids,
       count(t) AS ticket_count,
       'K-Means' AS algorithm
ORDER BY ticket_count DESC;

// Get tickets in Cluster B (DBSCAN, 500 tickets per cluster)
MATCH (t:Ticket)-[r:BELONGS_TO]->(c:Cluster {type: 'B'})
RETURN c.id AS cluster_id,
       c.label AS cluster_label,
       collect(t.id) AS ticket_ids,
       count(t) AS ticket_count,
       'DBSCAN' AS algorithm
ORDER BY ticket_count DESC;

// Get tickets in Cluster C (Agglomerative, 1000 tickets per cluster)
MATCH (t:Ticket)-[r:BELONGS_TO]->(c:Cluster {type: 'C'})
RETURN c.id AS cluster_id,
       c.label AS cluster_label,
       collect(t.id) AS ticket_ids,
       count(t) AS ticket_count,
       'Agglomerative Clustering' AS algorithm
ORDER BY ticket_count DESC;

// ----------------------------------------------------------------------------
// 5. DETAILED CLUSTER INFORMATION
// ----------------------------------------------------------------------------

// Get detailed info for a specific cluster (A, K-Means, cluster 0)
MATCH (c:Cluster {id: 'A_cluster_0', type: 'A'})
OPTIONAL MATCH (t:Ticket)-[r:BELONGS_TO]->(c)
RETURN c.id AS cluster_id,
       c.label AS cluster_label,
       c.ticket_count AS total_tickets,
       c.dominant_category AS dominant_category,
       c.categories AS all_categories,
       'K-Means' AS algorithm,
       collect({
         ticket_id: t.id,
         title: t.title,
         category: t.category,
         priority: t.priority
       }) AS tickets
LIMIT 1;

// Get cluster statistics for A (K-Means, 100 tickets per cluster)
MATCH (c:Cluster {type: 'A'})
RETURN count(c) AS num_clusters,
       avg(c.ticket_count) AS avg_tickets_per_cluster,
       min(c.ticket_count) AS min_tickets,
       max(c.ticket_count) AS max_tickets,
       sum(c.ticket_count) AS total_tickets,
       'K-Means' AS algorithm;

// Get cluster statistics for B (DBSCAN, 500 tickets per cluster)
MATCH (c:Cluster {type: 'B'})
RETURN count(c) AS num_clusters,
       avg(c.ticket_count) AS avg_tickets_per_cluster,
       min(c.ticket_count) AS min_tickets,
       max(c.ticket_count) AS max_tickets,
       sum(c.ticket_count) AS total_tickets,
       'DBSCAN' AS algorithm;

// Get cluster statistics for C (Agglomerative, 1000 tickets per cluster)
MATCH (c:Cluster {type: 'C'})
RETURN count(c) AS num_clusters,
       avg(c.ticket_count) AS avg_tickets_per_cluster,
       min(c.ticket_count) AS min_tickets,
       max(c.ticket_count) AS max_tickets,
       sum(c.ticket_count) AS total_tickets,
       'Agglomerative Clustering' AS algorithm;

// ----------------------------------------------------------------------------
// 6. COMPARISON QUERIES (All 9 combinations)
// ----------------------------------------------------------------------------

// Compare all clustering combinations - cluster counts
// Note: Algorithm is determined by type (A=K-Means, B=DBSCAN, C=Agglomerative)
MATCH (c:Cluster)
RETURN c.type AS subset_type,
       CASE 
         WHEN c.type = 'A' THEN 'K-Means'
         WHEN c.type = 'B' THEN 'DBSCAN'
         WHEN c.type = 'C' THEN 'Agglomerative Clustering'
       END AS algorithm,
       count(c) AS num_clusters,
       avg(c.ticket_count) AS avg_cluster_size,
       min(c.ticket_count) AS min_size,
       max(c.ticket_count) AS max_size
ORDER BY c.type;

// Compare all clustering combinations - category distribution
MATCH (c:Cluster)
UNWIND c.categories AS category
RETURN c.type AS subset_type,
       CASE 
         WHEN c.type = 'A' THEN 'K-Means'
         WHEN c.type = 'B' THEN 'DBSCAN'
         WHEN c.type = 'C' THEN 'Agglomerative Clustering'
       END AS algorithm,
       category,
       count(*) AS category_count
ORDER BY c.type, category_count DESC;

// ----------------------------------------------------------------------------
// 7. VISUALIZATION QUERIES (for Neo4j Browser)
// ----------------------------------------------------------------------------

// Visualize cluster graph for A (K-Means, 100 tickets per cluster)
MATCH (c:Cluster {type: 'A'})
OPTIONAL MATCH (t:Ticket)-[r:BELONGS_TO]->(c)
RETURN c, t, r
LIMIT 200;

// Visualize cluster graph for B (DBSCAN, 500 tickets per cluster)
MATCH (c:Cluster {type: 'B'})
OPTIONAL MATCH (t:Ticket)-[r:BELONGS_TO]->(c)
RETURN c, t, r
LIMIT 200;

// Visualize cluster graph for C (Agglomerative, 1000 tickets per cluster)
MATCH (c:Cluster {type: 'C'})
OPTIONAL MATCH (t:Ticket)-[r:BELONGS_TO]->(c)
RETURN c, t, r
LIMIT 200;

// ----------------------------------------------------------------------------
// 8. PERFORMANCE METRICS QUERIES
// ----------------------------------------------------------------------------

// Get all clustering metrics (if stored in Cluster nodes)
// Note: These properties may not exist - they're computed at runtime
MATCH (c:Cluster)
RETURN c.type AS subset_type,
       CASE 
         WHEN c.type = 'A' THEN 'K-Means'
         WHEN c.type = 'B' THEN 'DBSCAN'
         WHEN c.type = 'C' THEN 'Agglomerative Clustering'
       END AS algorithm,
       count(c) AS num_clusters,
       avg(c.ticket_count) AS avg_cluster_size
ORDER BY c.type;

// ----------------------------------------------------------------------------
// 9. SEARCH TICKETS BY QUERY (requires embedding computation)
// ----------------------------------------------------------------------------

// Get tickets for clustering demo (top 1000 by similarity)
// Note: This requires computing query embedding in Python first
// Then use this structure:

// MATCH (t:Ticket)
// WHERE t.id IN $ticket_ids  // Pass from Python after similarity search
// RETURN t.id AS ticket_id,
//        t.title AS title,
//        t.description AS description,
//        t.category AS category,
//        t.priority AS priority,
//        t.status AS status,
//        t.embedding_vector AS embedding_vector
// ORDER BY t.id
// LIMIT 1000;

// ----------------------------------------------------------------------------
// 10. HELPER QUERIES
// ----------------------------------------------------------------------------

// Count tickets with embeddings
MATCH (t:Ticket)
WHERE t.embedding_vector IS NOT NULL
RETURN count(t) AS tickets_with_embeddings;

// Count total tickets
MATCH (t:Ticket)
RETURN count(t) AS total_tickets;

// Get ticket categories distribution
MATCH (t:Ticket)
WHERE t.category IS NOT NULL
RETURN t.category AS category,
       count(*) AS count
ORDER BY count DESC
LIMIT 20;

// Check if Cluster nodes exist and what properties they have
MATCH (c:Cluster)
RETURN count(c) AS total_clusters,
       collect(DISTINCT c.type) AS cluster_types,
       collect(DISTINCT c.granularity_level) AS granularity_levels,
       keys(c) AS available_properties
LIMIT 1;

// Get all cluster types with their corresponding algorithms
MATCH (c:Cluster)
RETURN DISTINCT c.type AS cluster_type,
       CASE 
         WHEN c.type = 'A' THEN 'K-Means (100 tickets/cluster)'
         WHEN c.type = 'B' THEN 'DBSCAN (500 tickets/cluster)'
         WHEN c.type = 'C' THEN 'Agglomerative Clustering (1000 tickets/cluster)'
       END AS algorithm_info,
       count(c) AS num_clusters
ORDER BY c.type;

