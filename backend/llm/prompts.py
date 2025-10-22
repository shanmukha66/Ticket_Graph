"""LLM prompt templates for general and graph RAG answers."""

# ==============================================================================
# GENERAL PROMPT - Help Desk Style Answer
# ==============================================================================

GENERAL_PROMPT = """You are a helpful technical support assistant for a software development team.

Your role is to provide clear, accurate, and actionable answers to questions about software issues, bugs, and technical problems. When answering:

1. **Be Clear and Concise**: Provide direct answers without unnecessary jargon
2. **Be Practical**: Focus on actionable solutions and next steps
3. **Be Structured**: Organize your answer with clear sections when appropriate
4. **Be Professional**: Maintain a helpful, supportive tone

Guidelines:
- If the question is ambiguous, provide the most likely interpretation
- If multiple solutions exist, present the most common or recommended approach first
- Include relevant technical details but explain them in accessible terms
- Suggest follow-up steps or related considerations when appropriate

Format your response in a clear, readable manner with:
- Short paragraphs
- Bullet points for lists
- Code examples if relevant (use markdown formatting)

User Question: {query}

Please provide a helpful answer:"""


# ==============================================================================
# GRAPH RAG PROMPT - Context-Based Answer with Citations
# ==============================================================================

GRAPH_RAG_PROMPT = """You are a technical support assistant with access to a knowledge base of similar past issues and their resolutions.

**IMPORTANT INSTRUCTIONS:**
1. Answer ONLY using information from the provided context below
2. CITE specific ticket IDs when referencing information (e.g., "According to PROJ-123...")
3. Reference community clusters when mentioning patterns across multiple tickets
4. Provide REASONING for your answer based on the relationships and patterns in the data
5. If the context doesn't contain enough information, say so clearly

**Context Structure:**
- **Similar Sections**: Relevant text excerpts from past tickets
- **Graph Connections**: Related tickets and their relationships
- **Community Clusters**: Groups of similar issues detected by graph analysis
- **Section Types**: Different aspects of tickets (summary, description, resolution, etc.)

---

**USER QUESTION:**
{query}

---

**RETRIEVED CONTEXT:**

{context}

---

**GRAPH ANALYSIS:**

{graph_info}

---

**COMMUNITY INSIGHTS:**

{community_info}

---

**INSTRUCTIONS FOR YOUR ANSWER:**

1. **Start with a direct answer** to the user's question

2. **Cite specific tickets** using this format:
   - "Based on ticket PROJ-123..."
   - "Similar issues in PROJ-456 and PROJ-789 show..."
   - "The resolution in PROJ-234 suggests..."

3. **Reference community patterns**:
   - "This is similar to issues in Cluster #2 (authentication problems)..."
   - "Multiple tickets in the same cluster show..."

4. **Provide reasoning**:
   - Explain WHY the tickets are related
   - Mention key sections that support your answer
   - Note any graph connections that reveal patterns

5. **Structure your answer**:
   - **Direct Answer**: (1-2 sentences addressing the question)
   - **Supporting Evidence**: (Citations from tickets with details)
   - **Why These Clusters?**: (Explain WHY these community clusters are relevant - what common patterns, terms, or themes bind them together)
   - **Related Patterns**: (Community/cluster insights if relevant)
   - **Recommended Actions**: (Based on successful resolutions)

6. **If information is insufficient**:
   - State clearly: "The available context doesn't contain sufficient information about..."
   - Mention what type of information would be needed
   - Suggest similar topics that are available in the knowledge base

**Your Answer:**"""


# ==============================================================================
# CONTEXT FORMATTING TEMPLATES
# ==============================================================================

CONTEXT_SECTION_TEMPLATE = """
### Section {index}: {ticket_id} - {section_key}
**Similarity Score**: {score:.3f}
**Text**: {text}
"""

GRAPH_INFO_TEMPLATE = """
**Connected Tickets**: {num_similar} similar tickets found
**Graph Hops**: {num_hops}-hop neighborhood explored
**Total Nodes Retrieved**: {num_nodes}
**Relationships**: {num_relationships} connections

**Top Connected Tickets**:
{top_tickets}
"""

COMMUNITY_INFO_TEMPLATE = """
**Involved Communities**: {num_communities} clusters identified

{community_details}
"""

COMMUNITY_DETAIL_TEMPLATE = """
**Cluster #{cluster_id}** ({size} tickets)
- **Theme**: {reason}
- **Representative Tickets**: {representatives}
- **Common Terms**: {terms}
"""


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def format_context_sections(sections, max_sections=10):
    """
    Format retrieved sections for the prompt.
    
    Args:
        sections: List of section results with text, metadata, score
        max_sections: Maximum sections to include
        
    Returns:
        Formatted context string
    """
    if not sections:
        return "No relevant context sections found."
    
    formatted = []
    for i, section in enumerate(sections[:max_sections], 1):
        text = CONTEXT_SECTION_TEMPLATE.format(
            index=i,
            ticket_id=section['metadata'].get('ticket_id', 'UNKNOWN'),
            section_key=section['metadata'].get('section_key', 'unknown'),
            score=section['score'],
            text=section['text'][:500]  # Truncate long texts
        )
        formatted.append(text)
    
    return '\n'.join(formatted)


def format_graph_info(graph_context):
    """
    Format graph analysis information for the prompt.
    
    Args:
        graph_context: Dictionary with nodes, relationships, and connections
        
    Returns:
        Formatted graph info string
    """
    if not graph_context:
        return "No graph analysis available."
    
    # Format top connected tickets
    top_tickets_list = []
    for ticket in graph_context.get('top_tickets', [])[:5]:
        top_tickets_list.append(
            f"  - {ticket['id']}: {ticket.get('summary', 'No summary')[:80]} "
            f"(connections: {ticket.get('degree', 0)})"
        )
    top_tickets = '\n'.join(top_tickets_list) if top_tickets_list else "  None"
    
    return GRAPH_INFO_TEMPLATE.format(
        num_similar=graph_context.get('num_similar', 0),
        num_hops=graph_context.get('num_hops', 1),
        num_nodes=graph_context.get('num_nodes', 0),
        num_relationships=graph_context.get('num_relationships', 0),
        top_tickets=top_tickets
    )


def format_community_info(community_context):
    """
    Format community/cluster information for the prompt.
    
    Args:
        community_context: List of community summaries
        
    Returns:
        Formatted community info string
    """
    if not community_context:
        return "No community analysis available."
    
    community_details = []
    for comm in community_context:
        representatives = ', '.join([
            t['id'] for t in comm.get('top_tickets', [])[:3]
        ])
        terms = ', '.join(comm.get('frequent_terms', [])[:5])
        
        detail = COMMUNITY_DETAIL_TEMPLATE.format(
            cluster_id=comm['community_id'],
            size=comm['size'],
            reason=comm.get('reason', 'Similar issues'),
            representatives=representatives or 'None',
            terms=terms or 'None'
        )
        community_details.append(detail)
    
    return COMMUNITY_INFO_TEMPLATE.format(
        num_communities=len(community_context),
        community_details='\n'.join(community_details)
    )


def build_graph_rag_prompt(query, sections, graph_context, community_context):
    """
    Build complete Graph RAG prompt with all context.
    
    Args:
        query: User query string
        sections: Retrieved sections from vector search
        graph_context: Graph analysis results
        community_context: Community detection results
        
    Returns:
        Complete formatted prompt
    """
    context = format_context_sections(sections)
    graph_info = format_graph_info(graph_context)
    community_info = format_community_info(community_context)
    
    return GRAPH_RAG_PROMPT.format(
        query=query,
        context=context,
        graph_info=graph_info,
        community_info=community_info
    )

