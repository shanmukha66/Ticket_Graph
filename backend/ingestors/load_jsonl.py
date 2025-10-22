"""JSONL data ingestion for JIRA issues."""
import json
import re
from typing import Dict, List, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
from backend.graph.build_graph import Neo4jGraph
from backend.retrieval.embedder import Embedder
from backend.retrieval.vector_store import VectorStore
from backend.utils.env import env


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text or text == 'null' or text == 'None':
        return ""
    
    text = str(text).strip()
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text


def extract_sections_from_json(data: Dict[str, Any], ticket_id: str) -> List[Dict[str, Any]]:
    """
    Extract sections from JSONL record based on schema template.
    
    Args:
        data: JSON record as dictionary
        ticket_id: Ticket ID for section IDs
        
    Returns:
        List of section dictionaries with id, key, text, ticket_id
    """
    sections = []
    
    # If there's a 'text' field with all content, use it
    if 'text' in data and data['text']:
        main_text = clean_text(data['text'])
        if main_text and len(main_text) >= 20:
            sections.append({
                'id': f"{ticket_id}_main_text",
                'key': 'issue_description',
                'text': main_text[:10000],  # Keep more text for better embeddings
                'ticket_id': ticket_id
            })
    
    # Schema mapping based on schema_template.yml
    section_mappings = {
        'issue_summary': ['summary', 'title', 'subject'],
        'issue_description': ['description', 'details', 'body'],
        'steps_to_reproduce': ['steps_to_reproduce', 'reproduction_steps', 'how_to_reproduce'],
        'root_cause': ['root_cause', 'cause', 'analysis', 'diagnosis'],
        'resolution': ['resolution', 'solution', 'fix', 'workaround'],
        'priority': ['priority', 'severity', 'urgency'],
        'comments': ['comments', 'notes', 'discussion']
    }
    
    for section_key, possible_fields in section_mappings.items():
        # Try to find the field in the data
        text = None
        for field in possible_fields:
            if field in data and data[field]:
                # Handle nested structures
                value = data[field]
                
                # If it's a list (e.g., comments), join them
                if isinstance(value, list):
                    if section_key == 'comments':
                        # Create separate section for each comment
                        for i, comment in enumerate(value[:10]):  # Limit to 10 comments
                            comment_text = clean_text(str(comment))
                            if comment_text and len(comment_text) >= 10:
                                section_id = f"{ticket_id}_{section_key}_{i}"
                                sections.append({
                                    'id': section_id,
                                    'key': f"{section_key}_{i}",
                                    'text': comment_text[:5000],
                                    'ticket_id': ticket_id
                                })
                        continue
                    else:
                        text = ' '.join(str(v) for v in value)
                elif isinstance(value, dict):
                    # Extract text from dict (e.g., {body: "..."})
                    text = value.get('body') or value.get('text') or str(value)
                else:
                    text = str(value)
                
                text = clean_text(text)
                if text:
                    break
        
        # Add section if text is substantial (skip if already added as comments)
        if text and len(text) >= 10 and section_key != 'comments':
            section_id = f"{ticket_id}_{section_key}"
            sections.append({
                'id': section_id,
                'key': section_key,
                'text': text[:5000],  # Limit to 5000 chars
                'ticket_id': ticket_id
            })
    
    return sections


def ingest_jsonl(
    jsonl_path: str = None,
    batch_size: int = 10000,  # MASSIVE batches for maximum speed
    max_rows: int = None
) -> Dict[str, Any]:
    """
    Ingest tickets from JSONL file.
    
    Args:
        jsonl_path: Path to JSONL file (default from env JSONL_PATH)
        batch_size: Batch size for database operations
        max_rows: Maximum rows to process (None for all)
        
    Returns:
        Dictionary with ingestion statistics
    """
    jsonl_path = jsonl_path or env("JSONL_PATH", "/mnt/data/jira_issues_rag.jsonl")
    
    print(f"\n{'='*70}")
    print(f"INGESTING JSONL: {jsonl_path}")
    print(f"{'='*70}")
    
    if not Path(jsonl_path).exists():
        raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")
    
    stats = {
        'tickets_loaded': 0,
        'sections_loaded': 0,
        'embeddings_generated': 0,
        'errors': 0
    }
    
    # Initialize services
    graph = Neo4jGraph()
    graph.connect()
    
    embedder = Embedder()
    embedder.load()
    
    vector_store = VectorStore(dimension=embedder.dimension)
    
    # Try to load existing vector store
    vector_store.load()
    
    try:
        # Read JSONL
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            ticket_batch = []
            section_batch = []
            embedding_texts = []
            embedding_metas = []
            
            for i, line in enumerate(f):
                if max_rows and i >= max_rows:
                    break
                
                try:
                    # Parse JSON
                    data = json.loads(line.strip())
                    
                    # Extract ticket ID
                    ticket_id = (
                        data.get('issue_key') or 
                        data.get('id') or 
                        data.get('key') or 
                        f"JSONL-{i}"
                    )
                    ticket_id = clean_text(ticket_id)
                    
                    if not ticket_id:
                        continue
                    
                    # Build ticket data
                    ticket_data = {
                        'id': ticket_id,
                        'project': clean_text(data.get('project', '')),
                        'priority': clean_text(data.get('priority', '')),
                        'status': clean_text(data.get('status', '')),
                        'issueType': clean_text(data.get('issue_type', data.get('type', ''))),
                        'created': clean_text(data.get('created', data.get('created_date', ''))),
                        'updated': clean_text(data.get('updated', data.get('updated_date', ''))),
                        'summary': clean_text(data.get('summary', ''))[:500],
                        'description': clean_text(data.get('description', ''))[:500],
                        'reporter': clean_text(data.get('reporter', '')),
                        'assignee': clean_text(data.get('assignee', ''))
                    }
                    
                    ticket_batch.append(ticket_data)
                    
                    # Extract sections
                    sections = extract_sections_from_json(data, ticket_id)
                    section_batch.extend(sections)
                    
                    # Collect texts for embedding
                    for section in sections:
                        embedding_texts.append(section['text'])
                        embedding_metas.append({
                            'ticket_id': section['ticket_id'],
                            'section_key': section['key'],
                            'section_id': section['id']
                        })
                    
                    # Process batch
                    if len(ticket_batch) >= batch_size:
                        # Upsert tickets
                        count = graph.batch_upsert_tickets(ticket_batch)
                        stats['tickets_loaded'] += count
                        
                        # Upsert sections
                        count = graph.batch_upsert_sections(section_batch)
                        stats['sections_loaded'] += count
                        
                        # Generate embeddings
                        if embedding_texts:
                            print(f"  Generating embeddings for {len(embedding_texts)} sections...")
                            embeddings = embedder.embed_documents(
                                embedding_texts,
                                normalize=True,
                                batch_size=1000,  # MASSIVE batch for maximum speed!
                                show_progress=True,  # Show progress bar
                                num_workers=8  # Use 8 parallel workers
                            )
                            
                            # Add to vector store
                            vector_store.add(
                                texts=embedding_texts,
                                embeddings=embeddings,
                                metadatas=embedding_metas
                            )
                            stats['embeddings_generated'] += len(embedding_texts)
                        
                        print(f"  Processed {stats['tickets_loaded']} tickets, "
                              f"{stats['sections_loaded']} sections")
                        
                        # Clear batches
                        ticket_batch = []
                        section_batch = []
                        embedding_texts = []
                        embedding_metas = []
                
                except json.JSONDecodeError as e:
                    print(f"  JSON decode error on line {i}: {e}")
                    stats['errors'] += 1
                    continue
                except Exception as e:
                    print(f"  Error processing line {i}: {e}")
                    stats['errors'] += 1
                    continue
            
            # Process remaining batch
            if ticket_batch:
                count = graph.batch_upsert_tickets(ticket_batch)
                stats['tickets_loaded'] += count
                
                count = graph.batch_upsert_sections(section_batch)
                stats['sections_loaded'] += count
                
                if embedding_texts:
                    print(f"  Generating final embeddings for {len(embedding_texts)} sections...")
                    embeddings = embedder.embed_documents(
                        embedding_texts,
                        normalize=True,
                        batch_size=1000,
                        show_progress=True,
                        num_workers=8
                    )
                    vector_store.add(
                        texts=embedding_texts,
                        embeddings=embeddings,
                        metadatas=embedding_metas
                    )
                    stats['embeddings_generated'] += len(embedding_texts)
        
        # Save vector store
        print("\nPersisting vector store...")
        vector_store.persist()
        
        # Print summary
        print(f"\n{'='*70}")
        print("JSONL INGESTION COMPLETE")
        print(f"{'='*70}")
        print(f"Tickets loaded: {stats['tickets_loaded']}")
        print(f"Sections loaded: {stats['sections_loaded']}")
        print(f"Embeddings generated: {stats['embeddings_generated']}")
        print(f"Errors: {stats['errors']}")
        print(f"{'='*70}\n")
    
    finally:
        graph.close()
    
    return stats


if __name__ == "__main__":
    # Test ingestion
    import sys
    
    jsonl_file = sys.argv[1] if len(sys.argv) > 1 else None
    max_rows = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    stats = ingest_jsonl(jsonl_file, max_rows=max_rows)
    print(f"\nIngestion complete: {stats}")

