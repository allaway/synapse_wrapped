"""
Command-line interface for Synapse Wrapped.
"""

import argparse
import sys
from pathlib import Path
from typing import List

from synapse_wrapped import generate_wrapped, generate_wrapped_batch


def read_usernames_from_file(file_path: str) -> List[str]:
    """Read usernames from a text file (one per line)."""
    with open(file_path, 'r') as f:
        usernames = [line.strip() for line in f if line.strip()]
    return usernames


def main():
    parser = argparse.ArgumentParser(
        description="Generate Synapse Wrapped visualizations for Synapse.org users"
    )
    
    parser.add_argument(
        "--username",
        type=str,
        help="Username or email of a single user to generate wrapped for"
    )
    
    parser.add_argument(
        "--batch",
        type=str,
        help="Path to text file with usernames (one per line) for batch processing"
    )
    
    parser.add_argument(
        "--year",
        type=int,
        help="Year to analyze (defaults to current year)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (for single user) or output directory (for batch)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to Snowflake config file (JSON format)"
    )
    
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Disable background audio in generated HTML"
    )
    
    parser.add_argument(
        "--timezone",
        type=str,
        default="America/Chicago",
        help="Timezone for hourly activity charts (default: America/Chicago). Examples: America/New_York, America/Los_Angeles, Europe/London, UTC"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.username and not args.batch:
        parser.error("Either --username or --batch must be provided")
    
    if args.username and args.batch:
        parser.error("Cannot specify both --username and --batch")
    
    # Load Snowflake config if provided
    snowflake_config = None
    if args.config:
        import json
        with open(args.config, 'r') as f:
            snowflake_config = json.load(f)
    
    # Generate wrapped
    try:
        if args.username:
            # Single user
            output_path = generate_wrapped(
                username=args.username,
                year=args.year,
                output_path=args.output,
                snowflake_config=snowflake_config,
                include_audio=not args.no_audio,
                timezone=args.timezone
            )
            print(f"✓ Generated wrapped for {args.username}: {output_path}")
        
        else:
            # Batch processing
            if not Path(args.batch).exists():
                print(f"Error: File '{args.batch}' not found")
                sys.exit(1)
            
            usernames = read_usernames_from_file(args.batch)
            if not usernames:
                print(f"Error: No usernames found in '{args.batch}'")
                sys.exit(1)
            
            output_files = generate_wrapped_batch(
                usernames=usernames,
                year=args.year,
                output_dir=args.output,
                snowflake_config=snowflake_config,
                include_audio=not args.no_audio
            )
            
            print(f"\n✓ Generated {len(output_files)} wrapped visualizations")
            print(f"  Output directory: {Path(output_files[0]).parent if output_files else 'N/A'}")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

