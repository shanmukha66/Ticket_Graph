"""
Generate mock Jira ticket data for testing and development.

This script creates realistic mock Jira tickets in both CSV and JSONL formats
that are compatible with the existing ingestion pipeline.
"""
import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import argparse


# Mock data templates
PROJECTS = ["PROJ", "DEV", "QA", "OPS", "SEC", "DOC", "API", "UI"]
PRIORITIES = ["Critical", "High", "Medium", "Low", "Blocker"]
STATUSES = ["Open", "In Progress", "Resolved", "Closed", "Reopened", "To Do", "Done"]
ISSUE_TYPES = ["Bug", "Task", "Story", "Epic", "Improvement", "Sub-task"]
USERS = [
    "john.doe", "jane.smith", "bob.jones", "alice.brown", "charlie.wilson",
    "diana.prince", "frank.miller", "grace.hopper", "henry.ford", "ivy.lee"
]

# Common issue categories for realistic content
ISSUE_CATEGORIES = {
    "authentication": {
        "summaries": [
            "User unable to login with SSO",
            "Authentication timeout after 30 minutes",
            "Password reset email not received",
            "OAuth token expiration issue",
            "Multi-factor authentication not working",
            "Session expired unexpectedly",
            "Invalid credentials error on valid login",
            "LDAP authentication failing"
        ],
        "descriptions": [
            "Users are reporting that they cannot authenticate using SSO. The error occurs after clicking the login button.",
            "After 30 minutes of inactivity, users are being logged out even though the session timeout is set to 60 minutes.",
            "Password reset emails are not being delivered to users' inboxes. Checked spam folders and email service logs.",
            "OAuth tokens are expiring before the configured expiration time, causing users to be logged out prematurely.",
            "MFA verification codes are not being accepted even when entered correctly within the time window.",
            "User sessions are expiring unexpectedly, causing users to lose their work and have to re-authenticate.",
            "Users with valid credentials are receiving 'Invalid username or password' errors when attempting to login.",
            "LDAP authentication is failing with connection timeout errors. The LDAP server appears to be reachable."
        ],
        "resolutions": [
            "Fixed SSO configuration in identity provider settings. Updated redirect URIs and certificate.",
            "Increased session timeout to match configured value. Fixed session validation logic.",
            "Resolved email delivery issue by updating SMTP server configuration and DNS records.",
            "Corrected OAuth token expiration calculation. Tokens now expire at the correct time.",
            "Fixed MFA code validation timing window. Codes are now accepted within the 60-second window.",
            "Resolved session expiration bug by fixing the session refresh mechanism.",
            "Fixed credential validation logic. Issue was with case-sensitive username comparison.",
            "Updated LDAP connection pool settings and increased timeout values. Authentication now works correctly."
        ]
    },
    "database": {
        "summaries": [
            "Database connection pool exhausted",
            "Slow query performance on user table",
            "Database deadlock detected",
            "Connection timeout during peak hours",
            "Index missing on frequently queried column",
            "Database migration failed",
            "Data corruption in transaction log",
            "Replication lag between primary and replica"
        ],
        "descriptions": [
            "Application is unable to acquire database connections from the pool. All connections are in use.",
            "Queries on the user table are taking over 5 seconds to complete. This affects user authentication.",
            "Deadlock detected when multiple transactions try to update the same records simultaneously.",
            "During peak traffic hours (9-11 AM), database connections are timing out after 30 seconds.",
            "Frequent queries on the 'created_at' column are slow because there's no index on this column.",
            "Database migration script failed halfway through execution, leaving the database in an inconsistent state.",
            "Transaction log shows corrupted entries. This may have been caused by a disk I/O error.",
            "Replication lag between primary and replica databases is over 10 seconds, causing read inconsistencies."
        ],
        "resolutions": [
            "Increased connection pool size from 20 to 50. Added connection monitoring and alerting.",
            "Added composite index on (user_id, created_at) columns. Query time reduced to <100ms.",
            "Implemented retry logic with exponential backoff for deadlock scenarios. Added deadlock detection logging.",
            "Optimized connection pool settings and added connection timeout handling. Peak hour performance improved.",
            "Created index on 'created_at' column. Query performance improved by 10x.",
            "Rolled back migration and fixed script. Re-ran migration successfully with proper error handling.",
            "Restored database from backup and verified data integrity. Added disk health monitoring.",
            "Optimized replication settings and network configuration. Replication lag reduced to <1 second."
        ]
    },
    "api": {
        "summaries": [
            "API rate limit exceeded error",
            "REST API endpoint returning 500 error",
            "API response time degradation",
            "CORS error when calling API from frontend",
            "API authentication token invalid",
            "Missing API documentation",
            "API versioning issue",
            "Webhook delivery failures"
        ],
        "descriptions": [
            "API is returning 429 (Too Many Requests) errors even when requests are within the documented rate limits.",
            "The /api/v1/users endpoint is returning 500 Internal Server Error for all GET requests.",
            "API response times have increased from 200ms to over 2 seconds in the past week.",
            "Frontend application cannot make API calls due to CORS policy errors. Preflight requests are failing.",
            "Valid API authentication tokens are being rejected with 'Invalid token' errors.",
            "API documentation is missing for several endpoints. Developers are unable to integrate with the API.",
            "API versioning is inconsistent. Some endpoints use /v1/ while others use /api/v1/.",
            "Webhooks are not being delivered to registered endpoints. Delivery attempts are failing silently."
        ],
        "resolutions": [
            "Fixed rate limit calculation bug. Rate limits now correctly track requests per minute.",
            "Resolved null pointer exception in user service. Added input validation and error handling.",
            "Identified N+1 query problem. Optimized database queries and added caching layer.",
            "Updated CORS configuration to allow requests from frontend domain. Added proper headers.",
            "Fixed token validation logic. Issue was with token expiration time calculation.",
            "Generated API documentation using OpenAPI/Swagger. Added examples and error responses.",
            "Standardized API versioning to use /api/v1/ prefix for all endpoints.",
            "Fixed webhook delivery mechanism. Added retry logic and delivery status tracking."
        ]
    },
    "frontend": {
        "summaries": [
            "Page not loading on mobile devices",
            "Button click not triggering action",
            "Infinite scroll causing memory leak",
            "Form validation not working",
            "CSS styles not applying correctly",
            "JavaScript error in console",
            "Image loading slowly",
            "Accessibility issue with screen readers"
        ],
        "descriptions": [
            "The dashboard page does not load on mobile devices. Users see a blank screen.",
            "The submit button on the registration form is not triggering the form submission action.",
            "Infinite scroll feature is causing memory leaks. Browser memory usage increases over time.",
            "Form validation is not preventing submission of invalid data. Error messages are not displayed.",
            "CSS styles are not being applied correctly in production build. Styles work in development.",
            "JavaScript error 'Cannot read property of undefined' is appearing in the browser console.",
            "Images on the product page are loading very slowly, affecting page load time.",
            "Screen readers cannot properly navigate the application. ARIA labels are missing."
        ],
        "resolutions": [
            "Fixed responsive CSS breakpoints. Added mobile-specific styles and tested on multiple devices.",
            "Fixed event handler binding issue. Button now correctly triggers form submission.",
            "Implemented proper cleanup of event listeners and DOM elements. Memory leak resolved.",
            "Fixed form validation logic. Error messages now display correctly for invalid inputs.",
            "Resolved CSS build configuration issue. Styles are now correctly bundled in production.",
            "Added null checks and error handling. JavaScript error resolved.",
            "Optimized images by compressing and using WebP format. Added lazy loading.",
            "Added ARIA labels and semantic HTML. Screen reader compatibility improved."
        ]
    },
    "performance": {
        "summaries": [
            "Application slow during peak hours",
            "Memory usage increasing over time",
            "CPU usage at 100%",
            "Disk I/O bottleneck",
            "Network latency issues",
            "Cache hit rate low",
            "Garbage collection pauses",
            "Database query optimization needed"
        ],
        "descriptions": [
            "Application response time increases significantly during peak traffic hours (2-4 PM).",
            "Memory usage gradually increases over time, eventually causing out-of-memory errors.",
            "CPU usage is consistently at 100%, causing application slowdowns and timeouts.",
            "Disk I/O operations are taking too long, causing application timeouts.",
            "Network latency between application servers and database is over 500ms.",
            "Cache hit rate is only 30%, causing excessive database queries.",
            "Garbage collection pauses are causing 2-3 second application freezes.",
            "Several database queries are taking over 10 seconds to complete."
        ],
        "resolutions": [
            "Added horizontal scaling with load balancer. Response times improved during peak hours.",
            "Fixed memory leak in event handler. Added memory monitoring and alerting.",
            "Optimized CPU-intensive operations. Added caching and reduced redundant calculations.",
            "Upgraded to SSD storage and optimized I/O operations. Disk performance improved.",
            "Optimized network configuration and moved database to same region. Latency reduced to <50ms.",
            "Improved cache key strategy and increased cache TTL. Hit rate increased to 85%.",
            "Tuned JVM garbage collection settings. GC pauses reduced to <200ms.",
            "Added database indexes and optimized query execution plans. Query time reduced to <1 second."
        ]
    }
}


def generate_random_date(start_days_ago: int = 365, end_days_ago: int = 0) -> str:
    """Generate a random date string in ISO format."""
    days_ago = random.randint(end_days_ago, start_days_ago)
    date = datetime.now() - timedelta(days=days_ago)
    return date.strftime("%Y-%m-%d %H:%M:%S")


def generate_ticket_id(project: str, index: int) -> str:
    """Generate a Jira-style ticket ID."""
    return f"{project}-{1000 + index}"


def generate_mock_ticket(index: int, category: str = None) -> Dict[str, Any]:
    """
    Generate a single mock Jira ticket.
    
    Args:
        index: Ticket index number
        category: Optional category to use (if None, random category is selected)
    
    Returns:
        Dictionary with ticket data
    """
    # Select random category if not specified
    if category is None:
        category = random.choice(list(ISSUE_CATEGORIES.keys()))
    
    category_data = ISSUE_CATEGORIES[category]
    project = random.choice(PROJECTS)
    ticket_id = generate_ticket_id(project, index)
    
    # Generate dates
    created = generate_random_date(start_days_ago=180, end_days_ago=0)
    # Updated is usually after created, sometimes same day
    days_after_created = random.randint(0, 30)
    updated = (datetime.strptime(created, "%Y-%m-%d %H:%M:%S") + 
               timedelta(days=days_after_created)).strftime("%Y-%m-%d %H:%M:%S")
    
    # Select issue details
    summary = random.choice(category_data["summaries"])
    description = random.choice(category_data["descriptions"])
    resolution = random.choice(category_data["resolutions"]) if random.random() > 0.3 else ""
    
    # Build ticket data
    ticket = {
        # Core fields
        "key": ticket_id,
        "id": ticket_id,
        "issue_key": ticket_id,
        "project": project,
        "project_key": project,
        "priority": random.choice(PRIORITIES),
        "status": random.choice(STATUSES),
        "type": random.choice(ISSUE_TYPES),
        "issue_type": random.choice(ISSUE_TYPES),
        "Issue Type": random.choice(ISSUE_TYPES),
        
        # Dates
        "created": created,
        "updated": updated,
        "created_date": created,
        "updated_date": updated,
        "Created": created,
        "Updated": updated,
        
        # Content
        "summary": summary,
        "title": summary,
        "Summary": summary,
        "description": description,
        "Description": description,
        
        # People
        "reporter": random.choice(USERS),
        "Reporter": random.choice(USERS),
        "reporter_id": random.choice(USERS),
        "assignee": random.choice(USERS) if random.random() > 0.2 else "",
        "Assignee": random.choice(USERS) if random.random() > 0.2 else "",
        "assignee_id": random.choice(USERS) if random.random() > 0.2 else "",
        
        # Additional fields for JSONL
        "steps_to_reproduce": f"1. Navigate to the affected area\n2. Perform the action\n3. Observe the issue" if random.random() > 0.5 else "",
        "root_cause": f"Root cause analysis indicates {category} related issue." if random.random() > 0.6 else "",
        "resolution": resolution,
        "comments": [
            f"Comment from {random.choice(USERS)}: Investigating this issue.",
            f"Update from {random.choice(USERS)}: Found potential solution."
        ] if random.random() > 0.4 else [],
        
        # Combined text for RAG (used by CSV loader)
        "text_for_rag": f"{summary}\n\n{description}\n\n{resolution}" if resolution else f"{summary}\n\n{description}"
    }
    
    return ticket


def generate_csv_data(num_tickets: int, output_path: str) -> None:
    """
    Generate CSV file with mock Jira tickets.
    
    Args:
        num_tickets: Number of tickets to generate
        output_path: Path to output CSV file
    """
    print(f"Generating {num_tickets} mock tickets in CSV format...")
    
    # CSV fields based on what the loader expects
    csv_fields = [
        "key", "project", "priority", "status", "type", "created", "updated",
        "title", "description", "reporter_id", "assignee_id", "text_for_rag"
    ]
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        
        for i in range(num_tickets):
            ticket = generate_mock_ticket(i)
            # Select only CSV fields
            csv_row = {field: ticket.get(field, "") for field in csv_fields}
            writer.writerow(csv_row)
            
            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{num_tickets} tickets...")
    
    print(f"✓ CSV file created: {output_path}")
    print(f"  Total tickets: {num_tickets}")


def generate_jsonl_data(num_tickets: int, output_path: str) -> None:
    """
    Generate JSONL file with mock Jira tickets.
    
    Args:
        num_tickets: Number of tickets to generate
        output_path: Path to output JSONL file
    """
    print(f"Generating {num_tickets} mock tickets in JSONL format...")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for i in range(num_tickets):
            ticket = generate_mock_ticket(i)
            # JSONL format - one JSON object per line
            f.write(json.dumps(ticket, ensure_ascii=False) + '\n')
            
            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{num_tickets} tickets...")
    
    print(f"✓ JSONL file created: {output_path}")
    print(f"  Total tickets: {num_tickets}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate mock Jira ticket data for testing"
    )
    parser.add_argument(
        "--num-tickets",
        type=int,
        default=1000,
        help="Number of tickets to generate (default: 1000)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./mnt/data",
        help="Output directory for generated files (default: ./mnt/data)"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["csv", "jsonl", "both"],
        default="both",
        help="Output format: csv, jsonl, or both (default: both)"
    )
    parser.add_argument(
        "--csv-filename",
        type=str,
        default="jira_issues_clean.csv",
        help="CSV output filename (default: jira_issues_clean.csv)"
    )
    parser.add_argument(
        "--jsonl-filename",
        type=str,
        default="jira_issues_rag.jsonl",
        help="JSONL output filename (default: jira_issues_rag.jsonl)"
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("MOCK JIRA TICKET DATA GENERATOR")
    print("=" * 70)
    print(f"Number of tickets: {args.num_tickets}")
    print(f"Output directory: {output_dir}")
    print(f"Format: {args.format}")
    print("=" * 70)
    print()
    
    if args.format in ["csv", "both"]:
        csv_path = output_dir / args.csv_filename
        generate_csv_data(args.num_tickets, str(csv_path))
        print()
    
    if args.format in ["jsonl", "both"]:
        jsonl_path = output_dir / args.jsonl_filename
        generate_jsonl_data(args.num_tickets, str(jsonl_path))
        print()
    
    print("=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nYou can now use these files for data ingestion:")
    if args.format in ["csv", "both"]:
        print(f"  CSV: {output_dir / args.csv_filename}")
    if args.format in ["jsonl", "both"]:
        print(f"  JSONL: {output_dir / args.jsonl_filename}")
    print("\nTo ingest the data, run:")
    print("  curl -X POST http://127.0.0.1:8001/ingest")
    print("=" * 70)


if __name__ == "__main__":
    main()


