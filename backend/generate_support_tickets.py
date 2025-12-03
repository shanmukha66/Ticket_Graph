"""
Generate 5000 realistic support tickets for clustering benchmarking.

Each ticket includes:
- id
- title
- description
- category (billing, login issue, bug, feature request, performance, etc.)
- priority (low/medium/high)
- status (open, in_progress, resolved, closed)
- created_at (timestamp over last 1-2 years)
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import argparse


# Support ticket categories
CATEGORIES = [
    "billing", "login issue", "bug", "feature request", "performance",
    "authentication", "database", "api", "frontend", "security",
    "payment", "account", "subscription", "email", "notification"
]

PRIORITIES = ["low", "medium", "high"]

STATUSES = ["open", "in_progress", "resolved", "closed"]

# Status distribution weights (more resolved/closed than open)
STATUS_WEIGHTS = {
    "open": 0.15,
    "in_progress": 0.20,
    "resolved": 0.35,
    "closed": 0.30
}

# Category-specific content templates
CATEGORY_TEMPLATES = {
    "billing": {
        "titles": [
            "Incorrect charge on credit card",
            "Subscription renewal failed",
            "Invoice not received",
            "Payment method declined",
            "Refund request processing",
            "Billing cycle confusion",
            "Tax calculation error",
            "Currency conversion issue"
        ],
        "descriptions": [
            "Customer reports being charged twice for the same subscription period. Transaction ID: {id}",
            "Automatic renewal failed despite valid payment method on file. Card expires in 6 months.",
            "Customer did not receive invoice for last billing cycle. Checked spam folder.",
            "Payment method was declined but card is valid and has sufficient funds.",
            "Customer requested refund for unused subscription period. Need to process within 7 days.",
            "Customer confused about billing cycle dates. Subscription shows different dates than expected.",
            "Tax amount calculated incorrectly for international customer. VAT should be 20% but shows 25%.",
            "Currency conversion showing incorrect amount. Customer paid in EUR but charged in USD at wrong rate."
        ]
    },
    "login issue": {
        "titles": [
            "Cannot login with email",
            "Password reset not working",
            "Account locked after failed attempts",
            "Two-factor authentication error",
            "SSO login failing",
            "Session expired too quickly",
            "Remember me not working",
            "Login redirect loop"
        ],
        "descriptions": [
            "User cannot login using registered email address. Error: 'Invalid credentials'",
            "Password reset link sent but not working when clicked. Link expires before user can use it.",
            "Account locked after 3 failed login attempts. User claims to have correct password.",
            "Two-factor authentication code not being accepted. Code is valid and within time window.",
            "Single sign-on (SSO) login redirects to error page. Works for other users in same organization.",
            "User session expires after 5 minutes instead of configured 30 minutes.",
            "Remember me checkbox not persisting login. User has to login every time they visit.",
            "Login page redirects in infinite loop. User cannot access dashboard after authentication."
        ]
    },
    "bug": {
        "titles": [
            "Application crashes on startup",
            "Data not saving correctly",
            "Button click does nothing",
            "Error message appears randomly",
            "Feature broken after update",
            "Display shows wrong information",
            "Export function not working",
            "Search returns no results"
        ],
        "descriptions": [
            "Application crashes immediately after launching. Error log shows null pointer exception.",
            "User enters data in form but it doesn't save. No error message displayed.",
            "Submit button appears clickable but doesn't trigger any action when clicked.",
            "Random error message 'Something went wrong' appears even when no action is taken.",
            "Feature that worked yesterday is now broken after latest application update.",
            "Dashboard displays incorrect user information. Shows data from different account.",
            "Export to CSV function generates empty file or file with corrupted data.",
            "Search functionality returns no results even when matching items exist in database."
        ]
    },
    "feature request": {
        "titles": [
            "Add dark mode theme",
            "Request bulk export feature",
            "Need mobile app version",
            "Request API access",
            "Add custom notification sounds",
            "Request calendar integration",
            "Need advanced filtering options",
            "Request multi-language support"
        ],
        "descriptions": [
            "User requests dark mode theme option to reduce eye strain during night usage.",
            "Customer needs ability to export multiple records at once instead of one at a time.",
            "Users frequently request mobile application for iOS and Android platforms.",
            "Enterprise customer needs API access to integrate with their internal systems.",
            "User wants ability to customize notification sounds for different alert types.",
            "Request integration with Google Calendar and Outlook for scheduling features.",
            "Advanced users need more filtering options beyond basic search functionality.",
            "International users request support for multiple languages in the interface."
        ]
    },
    "performance": {
        "titles": [
            "Page loads very slowly",
            "Application freezes frequently",
            "High memory usage",
            "Database queries slow",
            "API response time degraded",
            "Image loading takes too long",
            "Report generation slow",
            "Bulk operations timeout"
        ],
        "descriptions": [
            "Dashboard page takes over 10 seconds to load. Other pages load normally.",
            "Application freezes for 2-3 seconds when switching between tabs.",
            "Memory usage increases over time and eventually causes out-of-memory errors.",
            "Database queries that used to take 100ms now take over 5 seconds.",
            "API endpoint response time increased from 200ms to 3 seconds in past week.",
            "Product images take 5+ seconds to load even on fast internet connection.",
            "Report generation that used to take 30 seconds now takes over 5 minutes.",
            "Bulk operations like deleting 100 items timeout after 60 seconds."
        ]
    },
    "authentication": {
        "titles": [
            "OAuth token expired",
            "API key authentication failing",
            "JWT token invalid",
            "Certificate validation error",
            "Multi-tenant auth issue",
            "Role-based access broken",
            "Permission denied error",
            "Token refresh not working"
        ],
        "descriptions": [
            "OAuth tokens expiring before configured expiration time. Users logged out prematurely.",
            "Valid API keys being rejected with 'Invalid API key' error message.",
            "JWT tokens showing as invalid even when freshly generated and not expired.",
            "SSL certificate validation failing for authentication endpoints.",
            "Multi-tenant authentication not properly isolating user data between tenants.",
            "Role-based access control not enforcing permissions correctly. Users accessing unauthorized resources.",
            "Permission denied errors appearing for users who should have access based on their role.",
            "Token refresh mechanism not working. Users cannot refresh expired tokens."
        ]
    },
    "database": {
        "titles": [
            "Connection pool exhausted",
            "Query timeout errors",
            "Data inconsistency detected",
            "Backup restoration failed",
            "Index missing causing slowness",
            "Transaction deadlock",
            "Replication lag increasing",
            "Database migration error"
        ],
        "descriptions": [
            "All database connections in pool are in use. Application cannot acquire new connections.",
            "Queries timing out after 30 seconds. Some queries used to complete in under 1 second.",
            "Data inconsistency between related tables. Foreign key constraints may be violated.",
            "Database backup restoration failed halfway through. Database left in inconsistent state.",
            "Frequent queries on unindexed columns causing full table scans and slow performance.",
            "Deadlock detected when multiple transactions try to update same records simultaneously.",
            "Replication lag between primary and replica databases increasing to over 10 seconds.",
            "Database migration script failed with error. Database schema partially updated."
        ]
    },
    "api": {
        "titles": [
            "Rate limit errors",
            "500 internal server error",
            "CORS policy violation",
            "Request timeout",
            "Missing API documentation",
            "Version deprecation notice",
            "Webhook delivery failure",
            "Response format changed"
        ],
        "descriptions": [
            "API returning 429 rate limit errors even when requests are within documented limits.",
            "API endpoint returning 500 internal server error for all requests.",
            "CORS policy blocking requests from frontend application. Preflight requests failing.",
            "API requests timing out after 30 seconds. Endpoint used to respond in under 1 second.",
            "API documentation missing for several endpoints. Developers cannot integrate properly.",
            "API version being deprecated but migration guide not clear. Breaking changes not documented.",
            "Webhooks not being delivered to registered endpoints. Delivery attempts failing silently.",
            "API response format changed without notice. Breaking existing client integrations."
        ]
    },
    "frontend": {
        "titles": [
            "Mobile responsive layout broken",
            "JavaScript errors in console",
            "CSS styles not loading",
            "Form validation not working",
            "Infinite scroll causing issues",
            "Accessibility problems",
            "Browser compatibility issue",
            "Image optimization needed"
        ],
        "descriptions": [
            "Mobile layout broken on iOS devices. Elements overlapping and not responsive.",
            "JavaScript errors appearing in browser console. 'Cannot read property of undefined'.",
            "CSS styles not applying correctly in production build. Works fine in development.",
            "Form validation not preventing submission of invalid data. Error messages not showing.",
            "Infinite scroll feature causing memory leaks. Browser memory usage increasing over time.",
            "Screen readers cannot properly navigate application. ARIA labels missing.",
            "Application not working correctly in Safari browser. Works fine in Chrome and Firefox.",
            "Images loading slowly and affecting page load time. Need compression and lazy loading."
        ]
    },
    "security": {
        "titles": [
            "Potential SQL injection vulnerability",
            "XSS attack detected",
            "Password policy too weak",
            "Session hijacking risk",
            "Data encryption missing",
            "Unauthorized access attempt",
            "Security audit findings",
            "Compliance requirement"
        ],
        "descriptions": [
            "Security scan detected potential SQL injection vulnerability in user input handling.",
            "Cross-site scripting (XSS) attack detected in user-generated content display.",
            "Password policy allows weak passwords. Need to enforce stronger requirements.",
            "Session tokens not properly secured. Risk of session hijacking attacks.",
            "Sensitive data being transmitted without encryption. Need HTTPS enforcement.",
            "Multiple unauthorized access attempts detected from suspicious IP addresses.",
            "Security audit found several vulnerabilities that need to be addressed.",
            "New compliance requirement (GDPR/SOC2) needs to be implemented in application."
        ]
    },
    "payment": {
        "titles": [
            "Payment gateway error",
            "Transaction declined",
            "Payment processing delay",
            "Refund not processed",
            "Currency mismatch",
            "Payment method update failed",
            "Subscription payment issue",
            "Invoice generation error"
        ],
        "descriptions": [
            "Payment gateway returning errors during checkout process. Transactions failing.",
            "Valid payment methods being declined by payment processor without clear reason.",
            "Payments taking longer than usual to process. Customers not receiving confirmation.",
            "Refund requested but not processed after 14 days. Customer still waiting.",
            "Payment currency not matching subscription currency. Conversion rate incorrect.",
            "Customer cannot update payment method. Error when saving new card details.",
            "Subscription payment failing on renewal date. Card is valid and has funds.",
            "Invoice generation failing for some customers. PDF not being created correctly."
        ]
    },
    "account": {
        "titles": [
            "Account creation failed",
            "Profile update error",
            "Account deletion request",
            "Email change not working",
            "Account merge needed",
            "Account suspension appeal",
            "Verification email not sent",
            "Account recovery issue"
        ],
        "descriptions": [
            "New account creation failing with error message. User cannot complete registration.",
            "Profile update saving changes but not persisting. Changes lost on page refresh.",
            "Customer requests account deletion but option not available in settings.",
            "Email change functionality not working. Verification email not being sent.",
            "Customer has two accounts and wants to merge them into one.",
            "Account suspended but customer claims violation was mistake. Wants to appeal.",
            "Account verification email not being sent. User cannot verify their account.",
            "Account recovery process not working. Password reset and email recovery both failing."
        ]
    },
    "subscription": {
        "titles": [
            "Subscription upgrade failed",
            "Downgrade not processed",
            "Trial extension request",
            "Cancellation not working",
            "Billing cycle confusion",
            "Feature access issue",
            "Subscription renewal error",
            "Plan migration problem"
        ],
        "descriptions": [
            "Customer trying to upgrade subscription but payment processing failing.",
            "Subscription downgrade requested but still being charged at old rate.",
            "Customer requests extension of trial period. Trial expired but wants more time.",
            "Subscription cancellation not working. Customer still being charged after cancellation.",
            "Customer confused about billing cycle dates. Subscription shows different dates than expected.",
            "Customer subscribed to plan but not getting access to promised features.",
            "Subscription renewal failing despite valid payment method on file.",
            "Migration between subscription plans not working correctly. Features not updating."
        ]
    },
    "email": {
        "titles": [
            "Email not being sent",
            "Emails going to spam",
            "Email delivery delay",
            "Wrong email template",
            "Unsubscribe not working",
            "Email formatting broken",
            "Bulk email failure",
            "Email bounce rate high"
        ],
        "descriptions": [
            "System emails not being sent to users. No errors in logs but emails not delivered.",
            "Legitimate emails being marked as spam by email providers. Need to fix SPF/DKIM records.",
            "Emails taking hours to deliver instead of seconds. Delivery queue backing up.",
            "Wrong email template being used for notifications. Users receiving incorrect content.",
            "Unsubscribe link not working. Users still receiving emails after unsubscribing.",
            "Email formatting broken in some email clients. HTML rendering incorrectly.",
            "Bulk email campaign failing. Only some recipients receiving emails.",
            "High email bounce rate. Many email addresses invalid or mailboxes full."
        ]
    },
    "notification": {
        "titles": [
            "Push notification not received",
            "Notification settings not saving",
            "Too many notifications",
            "Notification sound missing",
            "Desktop notification broken",
            "Mobile notification delay",
            "Notification permission denied",
            "Custom notification not working"
        ],
        "descriptions": [
            "Push notifications not being received on mobile devices. Settings appear correct.",
            "Notification preferences not saving. User changes settings but they revert.",
            "Users receiving too many notifications. Need better notification frequency controls.",
            "Notification sound not playing even when enabled in settings.",
            "Desktop browser notifications not appearing. Permission granted but notifications not showing.",
            "Mobile notifications arriving with significant delay. Not real-time as expected.",
            "Notification permission denied but user wants to enable. Cannot change permission.",
            "Custom notification rules not working. Users not receiving notifications based on custom criteria."
        ]
    }
}


def generate_ticket_id(index: int) -> str:
    """Generate a unique ticket ID."""
    return f"TICKET-{10000 + index}"


def generate_timestamp(start_days_ago: int = 365, end_days_ago: int = 0) -> str:
    """
    Generate a random timestamp in ISO format.
    
    Args:
        start_days_ago: Maximum days ago (e.g., 730 for 2 years)
        end_days_ago: Minimum days ago (e.g., 0 for today)
    """
    days_ago = random.randint(end_days_ago, start_days_ago)
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)
    seconds_ago = random.randint(0, 59)
    
    timestamp = datetime.now() - timedelta(
        days=days_ago,
        hours=hours_ago,
        minutes=minutes_ago,
        seconds=seconds_ago
    )
    return timestamp.isoformat()


def generate_status() -> str:
    """Generate status based on weighted distribution."""
    statuses = list(STATUS_WEIGHTS.keys())
    weights = list(STATUS_WEIGHTS.values())
    return random.choices(statuses, weights=weights)[0]


def generate_support_ticket(index: int, category: str = None) -> Dict[str, Any]:
    """
    Generate a single support ticket.
    
    Args:
        index: Ticket index number
        category: Optional category (if None, random category is selected)
    
    Returns:
        Dictionary with ticket data
    """
    if category is None:
        category = random.choice(CATEGORIES)
    
    templates = CATEGORY_TEMPLATES.get(category, CATEGORY_TEMPLATES["bug"])
    
    ticket_id = generate_ticket_id(index)
    title = random.choice(templates["titles"])
    
    # Add variety to descriptions by sometimes combining multiple templates
    base_description = random.choice(templates["descriptions"])
    if random.random() < 0.3:  # 30% chance to add additional context
        additional_context = random.choice([
            " This issue started occurring after the recent system update.",
            " Multiple users have reported similar problems.",
            " The issue seems to be intermittent and hard to reproduce consistently.",
            " Customer has provided screenshots and error logs for investigation.",
            " This is affecting multiple accounts in the same organization.",
            " The problem occurs specifically on mobile devices.",
            " This appears to be a regression from a previous working version.",
            " Customer is unable to complete their workflow due to this issue."
        ])
        description = base_description.format(id=ticket_id) + additional_context
    else:
        description = base_description.format(id=ticket_id)
    
    priority = random.choice(PRIORITIES)
    status = generate_status()
    
    # Generate timestamp over last 1-2 years (365-730 days ago)
    timestamp = generate_timestamp(start_days_ago=730, end_days_ago=0)
    
    # For resolved/closed tickets, add a more recent updated timestamp
    created_at = timestamp
    if status in ["resolved", "closed"]:
        # Resolved/closed tickets should have been created earlier
        created_at = generate_timestamp(start_days_ago=730, end_days_ago=30)
    
    return {
        "id": ticket_id,
        "title": title,
        "description": description,
        "category": category,
        "priority": priority,
        "status": status,
        "created_at": created_at,
        "timestamp": created_at  # Keep for backward compatibility
    }


def generate_tickets_jsonl(num_tickets: int, output_path: str) -> None:
    """
    Generate JSONL file with support tickets.
    
    Args:
        num_tickets: Number of tickets to generate
        output_path: Path to output JSONL file
    """
    print(f"Generating {num_tickets} support tickets...")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Distribute tickets across categories
    tickets_per_category = num_tickets // len(CATEGORIES)
    remaining = num_tickets % len(CATEGORIES)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        ticket_index = 0
        
        for category in CATEGORIES:
            # Add extra tickets to first few categories if there's a remainder
            count = tickets_per_category + (1 if remaining > 0 else 0)
            remaining -= 1
            
            for i in range(count):
                ticket = generate_support_ticket(ticket_index, category)
                f.write(json.dumps(ticket, ensure_ascii=False) + '\n')
                ticket_index += 1
                
                if ticket_index % 500 == 0:
                    print(f"  Generated {ticket_index}/{num_tickets} tickets...")
    
    print(f"✓ JSONL file created: {output_path}")
    print(f"  Total tickets: {num_tickets}")
    print(f"  Categories: {len(CATEGORIES)}")
    print(f"  Average tickets per category: {num_tickets // len(CATEGORIES)}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate mock support tickets for clustering benchmarking"
    )
    parser.add_argument(
        "--num-tickets",
        type=int,
        default=5000,
        help="Number of tickets to generate (default: 5000)"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="./mnt/data/support_tickets.jsonl",
        help="Output file path (default: ./mnt/data/support_tickets.jsonl)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("SUPPORT TICKET DATA GENERATOR")
    print("=" * 70)
    print(f"Number of tickets: {args.num_tickets}")
    print(f"Output file: {args.output_path}")
    print("=" * 70)
    print()
    
    generate_tickets_jsonl(args.num_tickets, args.output_path)
    
    print()
    print("=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nTickets saved to: {args.output_path}")
    print("\nNext steps:")
    print("1. Run clustering: python3 backend/cluster_tickets.py")
    print("2. Ingest into Neo4j: python3 backend/ingest_clustered_tickets.py")
    print("=" * 70)


if __name__ == "__main__":
    main()

