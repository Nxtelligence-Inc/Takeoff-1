#!/usr/bin/env python3
"""
Example script for processing ICF metrics from perimeter wall extractor output.

This script demonstrates how to:
1. Run the perimeter wall extractor
2. Load and process the resulting JSON data
3. Generate a simple report for ICF estimation

Usage:
    python examples/process_icf_metrics.py <image_path>
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def run_perimeter_extractor(image_path):
    """Run the perimeter wall extractor with LLM dimension extraction."""
    print(f"Processing foundation plan: {image_path}")
    
    # Run the perimeter wall extractor script in non-interactive mode
    env = os.environ.copy()
    env["NON_INTERACTIVE"] = "true"
    
    cmd = [
        "python", 
        "src/perimeter_wall_extractor.py", 
        image_path, 
        "--use_llm",
        "--no_visualize"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        print("Error running perimeter wall extractor:")
        print(result.stderr)
        sys.exit(1)
    
    print("Perimeter wall extraction completed successfully.")
    return "outputs/perimeter_walls.json"

def load_perimeter_data(json_path):
    """Load the perimeter data from the JSON file."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading JSON data: {e}")
        sys.exit(1)

def generate_icf_report(perimeter_data):
    """Generate a simple report for ICF estimation."""
    # Extract metrics
    metrics = perimeter_data.get('icf_metrics', {})
    assumptions = metrics.get('assumptions', {})
    
    # Create report
    report = []
    report.append("=" * 60)
    report.append("ICF FOUNDATION ESTIMATION REPORT")
    report.append("=" * 60)
    report.append("")
    
    # Project dimensions
    report.append("PROJECT DIMENSIONS:")
    report.append(f"  Overall Width: {perimeter_data.get('walls', [])[7].get('length', 'N/A')}")
    report.append(f"  Bounding Box: {metrics.get('bounding_box', {}).get('width_feet', 'N/A')} ft × {metrics.get('bounding_box', {}).get('length_feet', 'N/A')} ft")
    report.append(f"  Wall Thickness: {perimeter_data.get('wall_thickness', 'N/A')}")
    report.append(f"  Wall Height: {assumptions.get('wall_height_feet', 'N/A')} ft")
    report.append("")
    
    # Material requirements
    report.append("MATERIAL REQUIREMENTS:")
    report.append(f"  Total Linear Feet: {metrics.get('total_linear_feet', 'N/A')} ft")
    report.append(f"  Total Wall Area: {metrics.get('wall_area_sqft', 'N/A')} sq ft")
    report.append(f"  Concrete Volume: {metrics.get('concrete_volume_cuyd', 'N/A')} cu yd")
    report.append("")
    
    # ICF form calculation
    if 'total_linear_feet' in metrics and 'wall_height_feet' in assumptions:
        try:
            linear_feet = float(metrics['total_linear_feet'])
            wall_height = float(assumptions['wall_height_feet'])
            form_height = float(assumptions.get('standard_icf_form_height_inches', 48)) / 12  # Convert to feet
            
            # Calculate number of form courses
            courses = round(wall_height / form_height)
            
            # Calculate number of forms per course (assuming 4ft forms)
            forms_per_course = round(linear_feet / 4)
            
            # Total forms
            total_forms = courses * forms_per_course
            
            report.append("ICF FORM ESTIMATE:")
            report.append(f"  Standard Forms: {total_forms} pieces")
            report.append(f"  Corner Forms: {metrics.get('total_corners', 0) * courses} pieces")
            report.append("")
        except (ValueError, TypeError):
            pass
    
    # Wall segments
    report.append("WALL SEGMENTS:")
    for wall in perimeter_data.get('walls', []):
        report.append(f"  Wall {wall.get('id', 'N/A')}: {wall.get('length', 'N/A')} (from corner {wall.get('start_corner_id', 'N/A')} to {wall.get('end_corner_id', 'N/A')})")
    
    report.append("")
    report.append("=" * 60)
    report.append("NOTE: This is an automated estimate. Professional verification is recommended.")
    report.append("=" * 60)
    
    return "\n".join(report)

def main():
    # Check arguments
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Create examples/output directory if it doesn't exist
    os.makedirs("examples/output", exist_ok=True)
    
    # Run the perimeter wall extractor
    json_path = run_perimeter_extractor(image_path)
    
    # Load the perimeter data
    perimeter_data = load_perimeter_data(json_path)
    
    # Generate the ICF report
    report = generate_icf_report(perimeter_data)
    
    # Save the report
    report_path = "examples/output/icf_estimation_report.txt"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"ICF estimation report saved to {report_path}")
    print("\nReport Preview:")
    print("-" * 60)
    print("\n".join(report.split("\n")[:15]) + "\n...")
    print("-" * 60)

if __name__ == "__main__":
    main()
