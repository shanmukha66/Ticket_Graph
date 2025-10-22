// Graph RAG - Graph Data Science Queries
// Community detection, embeddings, and graph algorithms using Neo4j GDS

// ==============================================================================
// GRAPH PROJECTIONS
// ==============================================================================

// -- project_ticket_graph --
// Project tickets connected by SIMILAR_TO relationships
// Native projection for better performance
CALL gds.graph.project(
    'ticket-similarity-graph',
    'Ticket',
    {
        SIMILAR_TO: {
            orientation: 'UNDIRECTED',
            properties: 'score'
        }
    }
);

// -- project_ticket_section_graph --
// Project tickets + sections for full graph analysis
CALL gds.graph.project(
    'ticket-section-graph',
    ['Ticket', 'Section'],
    {
        SIMILAR_TO: {
            type: 'SIMILAR_TO',
            orientation: 'UNDIRECTED',
            properties: 'score'
        },
        HAS_SECTION: {
            type: 'HAS_SECTION',
            orientation: 'NATURAL'
        }
    }
);

// -- drop_projection --
// Drop a graph projection when done
// Parameters: graph_name
CALL gds.graph.drop($graph_name) YIELD graphName;


// ==============================================================================
// LOUVAIN COMMUNITY DETECTION
// ==============================================================================

// -- louvain_stream --
// Stream Louvain results (does not write to graph)
// Parameters: graph_name (default: 'ticket-similarity-graph')
CALL gds.louvain.stream('ticket-similarity-graph', {
    relationshipWeightProperty: 'score'
})
YIELD nodeId, communityId, intermediateCommunityIds
RETURN gds.util.asNode(nodeId).id AS ticketId, 
       communityId,
       intermediateCommunityIds;

// -- louvain_write --
// Run Louvain and write communityId back to Ticket nodes
CALL gds.louvain.write('ticket-similarity-graph', {
    writeProperty: 'communityId',
    relationshipWeightProperty: 'score',
    includeIntermediateCommunities: false
})
YIELD communityCount, modularity, modularities;

// -- louvain_stats --
// Get statistics about Louvain communities
CALL gds.louvain.stats('ticket-similarity-graph', {
    relationshipWeightProperty: 'score'
})
YIELD communityCount, modularity, modularities
RETURN communityCount, modularity, modularities;


// ==============================================================================
// LEIDEN COMMUNITY DETECTION (if available)
// ==============================================================================

// -- leiden_stream --
// Stream Leiden results (more accurate than Louvain)
CALL gds.leiden.stream('ticket-similarity-graph', {
    relationshipWeightProperty: 'score',
    gamma: 1.0,
    theta: 0.01
})
YIELD nodeId, communityId, intermediateCommunityIds
RETURN gds.util.asNode(nodeId).id AS ticketId, 
       communityId,
       intermediateCommunityIds;

// -- leiden_write --
// Run Leiden and write communityId to nodes
CALL gds.leiden.write('ticket-similarity-graph', {
    writeProperty: 'communityId',
    relationshipWeightProperty: 'score',
    includeIntermediateCommunities: false
})
YIELD communityCount, modularity, modularities;


// ==============================================================================
// PAGERANK (Optional)
// ==============================================================================

// -- pagerank_stream --
// Run PageRank to identify important tickets
CALL gds.pageRank.stream('ticket-similarity-graph', {
    relationshipWeightProperty: 'score',
    dampingFactor: 0.85
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).id AS ticketId, 
       score AS pageRankScore
ORDER BY score DESC;

// -- pagerank_write --
// Write PageRank scores to nodes
CALL gds.pageRank.write('ticket-similarity-graph', {
    writeProperty: 'pageRank',
    relationshipWeightProperty: 'score',
    dampingFactor: 0.85
})
YIELD nodePropertiesWritten, ranIterations;


// ==============================================================================
// NODE EMBEDDINGS (Optional - FastRP)
// ==============================================================================

// -- fastrp_stream --
// Generate node embeddings using FastRP
CALL gds.fastRP.stream('ticket-similarity-graph', {
    embeddingDimension: 128,
    relationshipWeightProperty: 'score',
    iterationWeights: [0.0, 1.0, 1.0]
})
YIELD nodeId, embedding
RETURN gds.util.asNode(nodeId).id AS ticketId, embedding;

// -- fastrp_write --
// Write embeddings to nodes
CALL gds.fastRP.write('ticket-similarity-graph', {
    writeProperty: 'embedding',
    embeddingDimension: 128,
    relationshipWeightProperty: 'score'
})
YIELD nodePropertiesWritten;


// ==============================================================================
// COMMUNITY ANALYSIS QUERIES
// ==============================================================================

// -- get_community_sizes --
// Get size of each community
MATCH (t:Ticket)
WHERE t.communityId IS NOT NULL
RETURN t.communityId AS communityId, 
       count(t) AS size
ORDER BY size DESC;

// -- get_community_members --
// Get all tickets in a specific community
// Parameters: community_id
MATCH (t:Ticket {communityId: $community_id})
OPTIONAL MATCH (t)-[:HAS_SECTION]->(s:Section)
RETURN t, collect(s) AS sections;

// -- get_top_tickets_per_community --
// Get top N tickets from each community (by PageRank or degree)
// Parameters: top_n
MATCH (t:Ticket)
WHERE t.communityId IS NOT NULL
WITH t.communityId AS communityId, t
ORDER BY coalesce(t.pageRank, 0) DESC
WITH communityId, collect(t)[0..$top_n] AS topTickets
RETURN communityId, topTickets;

// -- get_community_text --
// Get all section text for a community (for term frequency analysis)
// Parameters: community_id
MATCH (t:Ticket {communityId: $community_id})-[:HAS_SECTION]->(s:Section)
RETURN collect(s.text) AS texts;

// -- community_connectivity --
// Analyze connectivity within and between communities
MATCH (t1:Ticket)-[r:SIMILAR_TO]->(t2:Ticket)
WHERE t1.communityId IS NOT NULL AND t2.communityId IS NOT NULL
WITH t1.communityId AS comm1, 
     t2.communityId AS comm2,
     count(r) AS edgeCount
RETURN comm1, 
       comm2,
       edgeCount,
       CASE WHEN comm1 = comm2 THEN 'internal' ELSE 'external' END AS edgeType
ORDER BY edgeCount DESC;


// ==============================================================================
// CLEANUP
// ==============================================================================

// -- remove_community_ids --
// Clear all communityId properties
MATCH (t:Ticket)
WHERE t.communityId IS NOT NULL
REMOVE t.communityId;

// -- remove_pagerank --
// Clear all PageRank scores
MATCH (t:Ticket)
WHERE t.pageRank IS NOT NULL
REMOVE t.pageRank;

