#!/usr/bin/env python3
"""
Example script for preparing foundation plan analysis results for database storage.

This script demonstrates how to:
1. Load analysis results from a JSON file
2. Prepare the data for database storage
3. Generate SQL statements for PostgreSQL
4. Generate payload for Supabase
5. Save the database-ready data to a file

Usage:
    python examples/prepare_for_database.py <json_path> [--project_id <project_id>] [--drawing_name <name>]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database_utils import (
    prepare_for_database,
    generate_postgresql_statements,
    generate_supabase_payload,
    save_database_ready_json
)

def main():
    parser = argparse.ArgumentParser(description="Prepare foundation plan analysis results for database storage.")
    parser.add_argument("json_path", help="Path to the analysis JSON file.")
    parser.add_argument("--project_id", help="Optional project identifier.")
    parser.add_argument("--drawing_name", help="Optional drawing name.")
    parser.add_argument("--output_dir", default="outputs/database", help="Output directory for database-ready files.")
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load the analysis data
    try:
        with open(args.json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        sys.exit(1)
    
    # Extract drawing name from file path if not provided
    drawing_name = args.drawing_name
    if not drawing_name:
        drawing_name = Path(args.json_path).stem
    
    print(f"Processing analysis data for drawing: {drawing_name}")
    
    # Prepare data for database
    db_ready_data = prepare_for_database(
        data,
        drawing_name=drawing_name,
        project_id=args.project_id
    )
    
    # Save database-ready JSON
    db_ready_path = os.path.join(args.output_dir, f"{drawing_name}_db_ready.json")
    save_database_ready_json(db_ready_data, db_ready_path)
    
    # Generate PostgreSQL statements
    sql_statements = generate_postgresql_statements(db_ready_data)
    
    # Save SQL statements
    sql_path = os.path.join(args.output_dir, f"{drawing_name}_postgresql.sql")
    with open(sql_path, 'w') as f:
        for table, sql in sql_statements.items():
            f.write(f"-- {table.upper()} TABLE\n")
            f.write(sql)
            f.write("\n\n")
    print(f"PostgreSQL statements saved to {sql_path}")
    
    # Generate Supabase payload
    supabase_payload = generate_supabase_payload(db_ready_data)
    
    # Save Supabase payload
    supabase_path = os.path.join(args.output_dir, f"{drawing_name}_supabase.json")
    with open(supabase_path, 'w') as f:
        json.dump(supabase_payload, f, indent=2)
    print(f"Supabase payload saved to {supabase_path}")
    
    # Print summary
    print("\nSUMMARY:")
    print(f"Analysis ID: {db_ready_data['metadata']['analysis_id']}")
    print(f"Timestamp: {db_ready_data['metadata']['timestamp']}")
    print(f"Drawing Name: {db_ready_data['metadata']['drawing_name']}")
    if args.project_id:
        print(f"Project ID: {args.project_id}")
    
    if 'icf_metrics' in data:
        print("\nICF METRICS:")
        metrics = data['icf_metrics']
        print(f"Total Linear Feet: {metrics.get('total_linear_feet', 'N/A')}")
        print(f"Total Corners: {metrics.get('total_corners', 'N/A')}")
        print(f"Wall Area: {metrics.get('wall_area_sqft', 'N/A')} sq ft")
        print(f"Concrete Volume: {metrics.get('concrete_volume_cuyd', 'N/A')} cu yd")
    
    print("\nFILES GENERATED:")
    print(f"1. Database-ready JSON: {db_ready_path}")
    print(f"2. PostgreSQL statements: {sql_path}")
    print(f"3. Supabase payload: {supabase_path}")
    
    print("\nNEXT STEPS:")
    print("1. Review the generated files to ensure the data is formatted correctly.")
    print("2. Use the PostgreSQL statements to insert the data into your database.")
    print("3. Or use the Supabase payload with the Supabase client to insert the data.")
    print("4. Refer to docs/database_integration.md for more information on database integration.")

if __name__ == "__main__":
    main()
