"""CSV data ingestion for JIRA issues."""
import csv
import re
from typing import Dict, List, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from backend.graph.build_graph import Neo4jGraph
from backend.retrieval.embedder import Embedder
from backend.retrieval.vector_store import VectorStore
from backend.utils.env import env


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text or text == 'nan' or text == 'None':
        return ""
    
    text = str(text).strip()
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text


def extract_sections_from_row(row: Dict[str, Any], ticket_id: str) -> List[Dict[str, Any]]:
    """
    Extract sections from CSV row based on schema template.
    
    Args:
        row: CSV row as dictionary
        ticket_id: Ticket ID for section IDs
        
    Returns:
        List of section dictionaries with id, key, text, ticket_id
    """
    sections = []
    
    # First, check if there's a text_for_rag field (main content field)
    if 'text_for_rag' in row and row['text_for_rag']:
        main_text = clean_text(row['text_for_rag'])
        if main_text and len(main_text) >= 20:
            section_id = f"{ticket_id}_text_for_rag"
            sections.append({
                'id': section_id,
                'key': 'text_for_rag',
                'text': main_text[:10000],  # Keep up to 10K chars
                'ticket_id': ticket_id
            })
    
    # Schema mapping based on schema_template.yml - support both formats
    section_mappings = {
        'issue_summary': ['title', 'summary', 'Summary', 'Title', 'Subject'],
        'issue_description': ['description', 'Description', 'Details'],
        'steps_to_reproduce': ['steps_to_reproduce', 'Steps to Reproduce', 'Reproduction Steps'],
        'root_cause': ['root_cause', 'Root Cause', 'Cause', 'Analysis'],
        'resolution': ['resolution', 'Resolution', 'Solution', 'Fix'],
        'priority': ['priority', 'Priority', 'Severity'],
        'comments': ['comments', 'Comment', 'Notes']
    }
    
    for section_key, possible_fields in section_mappings.items():
        # Try to find the field in the row
        text = None
        for field in possible_fields:
            if field in row and row[field]:
                text = clean_text(row[field])
                break
        
        # Add section if text is substantial
        if text and len(text) >= 10:
            section_id = f"{ticket_id}_{section_key}"
            sections.append({
                'id': section_id,
                'key': section_key,
                'text': text[:5000],  # Limit to 5000 chars
                'ticket_id': ticket_id
            })
    
    return sections


def ingest_csv(
    csv_path: str = None,
    batch_size: int = 10000,  # MASSIVE batches for maximum speed
    max_rows: int = None
) -> Dict[str, Any]:
    """
    Ingest tickets from CSV file.
    
    Args:
        csv_path: Path to CSV file (default from env CSV_PATH)
        batch_size: Batch size for database operations
        max_rows: Maximum rows to process (None for all)
        
    Returns:
        Dictionary with ingestion statistics
    """
    csv_path = csv_path or env("CSV_PATH", "/mnt/data/jira_issues_clean.csv")
    
    print(f"\n{'='*70}")
    print(f"INGESTING CSV: {csv_path}")
    print(f"{'='*70}")
    
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
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
        # Read CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            ticket_batch = []
            section_batch = []
            embedding_texts = []
            embedding_metas = []
            
            for i, row in enumerate(reader):
                if max_rows and i >= max_rows:
                    break
                
                try:
                    # Extract ticket ID - support both JIRA export and database formats
                    ticket_id = (row.get('key') or row.get('Issue key') or 
                                row.get('id') or row.get('Key') or f"CSV-{i}")
                    ticket_id = clean_text(ticket_id)
                    
                    if not ticket_id:
                        continue
                    
                    # Build ticket data - support both formats
                    ticket_data = {
                        'id': ticket_id,
                        'project': clean_text(row.get('project') or row.get('Project key', '')),
                        'priority': clean_text(row.get('priority') or row.get('Priority', '')),
                        'status': clean_text(row.get('status') or row.get('Status', '')),
                        'issueType': clean_text(row.get('type') or row.get('Issue Type', '')),
                        'created': clean_text(row.get('created') or row.get('Created', '')),
                        'updated': clean_text(row.get('updated') or row.get('Updated', '')),
                        'summary': clean_text(row.get('title') or row.get('Summary', '')),
                        'description': clean_text(row.get('description') or row.get('Description', ''))[:500],  # Truncate
                        'reporter': clean_text(row.get('reporter_id') or row.get('Reporter', '')),
                        'assignee': clean_text(row.get('assignee_id') or row.get('Assignee', ''))
                    }
                    
                    ticket_batch.append(ticket_data)
                    
                    # Extract sections
                    sections = extract_sections_from_row(row, ticket_id)
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
                        
                        # Generate embeddings (parallel batch processing)
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
                
                except Exception as e:
                    print(f"  Error processing row {i}: {e}")
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
        print("CSV INGESTION COMPLETE")
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
    
    csv_file = sys.argv[1] if len(sys.argv) > 1 else None
    max_rows = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    stats = ingest_csv(csv_file, max_rows=max_rows)
    print(f"\nIngestion complete: {stats}")

