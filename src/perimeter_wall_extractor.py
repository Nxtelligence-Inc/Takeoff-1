#!/usr/bin/env python3
"""
Perimeter Wall Extractor

This script extracts the perimeter walls from a foundation plan using
image processing techniques that focus specifically on thick outer walls.
It provides an alternative approach to the existing ICF perimeter extractor.

Usage:
    python perimeter_wall_extractor.py <image_path> --overall_width <width> [--output_dir <dir>] [--show_steps]
    python perimeter_wall_extractor.py <image_path> --overall_width <width> --export_db [--project_id <id>]

Example:
    python perimeter_wall_extractor.py src/Screenshot.png --overall_width "55'-0\"" --show_steps
    python perimeter_wall_extractor.py src/Screenshot.png --use_llm --export_db --project_id "project123"
"""

import os
import argparse
import cv2
import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path
from typing import Tuple, Dict, List, Any, Optional, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import database utilities
try:
    from database_utils import (
        prepare_for_database,
        generate_postgresql_statements,
        generate_supabase_payload,
        save_database_ready_json
    )
except ImportError:
    # Database utilities are optional
    pass

# Import necessary functions from vision_module
from vision_module import (
    feet_inches_to_inches,
    calculate_scale_factor,
    calculate_wall_lengths,
    visualize_icf_perimeter
)

def extract_perimeter_walls(image_path: str, show_steps: bool = False) -> Tuple[np.ndarray, Dict[str, Any], np.ndarray]:
    """
    Extracts only the thick perimeter walls from a foundation plan.
    
    Args:
        image_path: Path to the foundation plan image.
        show_steps: Whether to save intermediate steps as images.
        
    Returns:
        perimeter_mask: Binary mask of the perimeter walls.
        geometry_data: Dictionary containing corner coordinates and wall segments.
        result_image: Visualization of the detected perimeter.
    """
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not open/find image: {image_path}")
    
    # Create output directory for steps if needed
    if show_steps:
        os.makedirs("perimeter_steps", exist_ok=True)
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply CLAHE to enhance contrast
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    if show_steps:
        cv2.imwrite("perimeter_steps/1_enhanced.png", enhanced)
    
    # Invert the image first to make walls black on white background
    inverted = cv2.bitwise_not(enhanced)
    if show_steps:
        cv2.imwrite("perimeter_steps/1.5_inverted.png", inverted)
    
    # Extract only the darkest pixels (walls) from the inverted image
    # Using a low threshold to isolate just the black walls
    _, dark_mask = cv2.threshold(inverted, 30, 255, cv2.THRESH_BINARY_INV)
    
    if show_steps:
        cv2.imwrite("perimeter_steps/2_dark_mask.png", dark_mask)
    
    # Invert the dark mask
    inverted_mask = cv2.bitwise_not(dark_mask)
    if show_steps:
        cv2.imwrite("perimeter_steps/2.05_inverted_mask.png", inverted_mask)
    
    # Apply Gaussian blur to the inverted mask with increased kernel size
    blurred_mask = cv2.GaussianBlur(inverted_mask, (9, 9), 0)
    if show_steps:
        cv2.imwrite("perimeter_steps/2.1_blurred_mask.png", blurred_mask)
    
    # Apply high threshold to get clean edges
    _, high_threshold_mask = cv2.threshold(blurred_mask, 200, 255, cv2.THRESH_BINARY)
    if show_steps:
        cv2.imwrite("perimeter_steps/2.2_high_threshold_mask.png", high_threshold_mask)
    
    # Create kernel for offset (3 pixels)
    offset_kernel = np.ones((7, 7), np.uint8)  # Size depends on desired offset
    
    # Create offset mask by dilating
    offset_mask = cv2.dilate(high_threshold_mask, offset_kernel, iterations=1)
    if show_steps:
        cv2.imwrite("perimeter_steps/2.3_offset_mask.png", offset_mask)
    
    # Apply the offset mask to the original image
    masked_original = cv2.bitwise_and(image, image, mask=offset_mask)
    if show_steps:
        cv2.imwrite("perimeter_steps/2.4_masked_original.png", masked_original)
    
    # Apply morphological operations to identify thick walls
    # Use a smaller kernel for erosion to preserve more wall details
    erosion_kernel = np.ones((3, 3), np.uint8)  # Smaller kernel to preserve more details
    dilation_kernel = np.ones((5, 5), np.uint8)  # Slightly larger kernel for dilation
    
    # Erosion will remove thin lines but keep thick walls
    # Using a smaller kernel and fewer iterations to preserve more wall details
    eroded = cv2.erode(high_threshold_mask, erosion_kernel, iterations=1)
    
    # Dilation to restore the original thickness
    thick_walls = cv2.dilate(eroded, dilation_kernel, iterations=1)
    
    if show_steps:
        cv2.imwrite("perimeter_steps/3_thick_walls.png", thick_walls)
    
    # Find contours in the thick walls image
    contours, _ = cv2.findContours(thick_walls, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create a mask for the perimeter
    perimeter_mask = np.zeros_like(thick_walls)
    
    # Find the largest contour (should be the perimeter)
    largest_contour = None
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Draw only the largest contour - use proper color tuple
        cv2.drawContours(perimeter_mask, [largest_contour], 0, (255,), thickness=cv2.FILLED)
        
        if show_steps:
            perimeter_vis = image.copy()
            cv2.drawContours(perimeter_vis, [largest_contour], 0, (0, 255, 0), 3)
            cv2.imwrite("perimeter_steps/4_perimeter_contour.png", perimeter_vis)
    else:
        print("No contours found. Check the image and threshold parameters.")
        return np.zeros_like(gray), {"corners": [], "walls": []}, image.copy()
    
    if show_steps:
        cv2.imwrite("perimeter_steps/5_perimeter_mask.png", perimeter_mask)
    
    # Thin the perimeter for precise corner detection
    # Note: This requires OpenCV contrib modules
    thinned_perimeter = perimeter_mask.copy()  # Default to original if thinning not available
    try:
        # Check if ximgproc is available
        if hasattr(cv2, 'ximgproc'):
            thinned_perimeter = cv2.ximgproc.thinning(perimeter_mask)  # type: ignore
            if show_steps:
                cv2.imwrite("perimeter_steps/6_thinned_perimeter.png", thinned_perimeter)
    except (AttributeError, ImportError):
        print("Warning: cv2.ximgproc not available. Skipping thinning step.")
    
    # Use approxPolyDP to get the corners directly from the contour
    # This should give us corners in the correct order around the perimeter
    epsilon = 0.01 * cv2.arcLength(largest_contour, True)
    corners = cv2.approxPolyDP(largest_contour, epsilon, True)
    
    # Create a visualization of the corners
    corner_vis = image.copy()
    for i, corner in enumerate(corners):
        x, y = corner.ravel()
        # Convert to int to avoid type errors
        x_int, y_int = int(x), int(y)
        cv2.circle(corner_vis, (x_int, y_int), 8, (0, 0, 255), -1)  # Red dot
        cv2.circle(corner_vis, (x_int, y_int), 8, (0, 0, 0), 2)     # Black outline
        
        # Add ID number - use integer coordinates
        cv2.putText(corner_vis, str(i), (x_int + 10, y_int + 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 5)  # White background
        cv2.putText(corner_vis, str(i), (x_int + 10, y_int + 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)        # Black text
    
    if show_steps:
        cv2.imwrite("perimeter_steps/7_perimeter_corners.png", corner_vis)
    
    # Create geometry data structure
    geometry_data = {
        "corners": [],
        "walls": []
    }
    
    # Print the number of corners for debugging
    print(f"Detected {len(corners)} corners with approxPolyDP")
    
    # Add corners to geometry data
    for i, corner in enumerate(corners):
        x, y = corner.ravel()
        geometry_data["corners"].append({
            "id": i,
            "x": int(x),
            "y": int(y)
        })
    
    # Add walls to geometry data
    for i in range(len(corners)):
        pt1 = corners[i].ravel()
        pt2 = corners[(i + 1) % len(corners)].ravel()
        
        # Calculate wall length in pixels
        length_pixels = np.sqrt((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)
        
        geometry_data["walls"].append({
            "id": i + 1,
            "start_corner_id": i,
            "end_corner_id": (i + 1) % len(corners),
            "start_x": int(pt1[0]),
            "start_y": int(pt1[1]),
            "end_x": int(pt2[0]),
            "end_y": int(pt2[1]),
            "length_pixels": length_pixels
        })
    
    # Create a visualization of the final result
    result_image = image.copy()
    
    # Draw the perimeter walls
    perimeter_overlay = cv2.cvtColor(perimeter_mask, cv2.COLOR_GRAY2BGR)
    perimeter_overlay[..., 0] = 0  # Set blue channel to 0
    perimeter_overlay[..., 2] = 0  # Set red channel to 0
    # Only keep green channel where walls are
    
    # Blend the perimeter overlay with the original image
    alpha = 0.5
    result_image = cv2.addWeighted(result_image, 1, perimeter_overlay, alpha, 0)
    
    # Draw corners and walls
    for i in range(len(geometry_data["corners"])):
        corner = geometry_data["corners"][i]
        next_corner = geometry_data["corners"][(i + 1) % len(geometry_data["corners"])]
        
        # Draw corner
        cv2.circle(result_image, (corner["x"], corner["y"]), 8, (0, 0, 255), -1)
        
        # Draw wall
        cv2.line(result_image, (corner["x"], corner["y"]), 
                (next_corner["x"], next_corner["y"]), (0, 255, 0), 3)
    
    if show_steps:
        cv2.imwrite("perimeter_steps/8_final_result.png", result_image)
    
    return perimeter_mask, geometry_data, result_image

def calculate_icf_metrics(perimeter_model: Dict[str, Any], wall_height: float = 8.0) -> Dict[str, Any]:
    """
    Calculate ICF-specific metrics for the foundation.
    
    Args:
        perimeter_model: Dictionary containing corners and walls data
        wall_height: Assumed wall height in feet (default: 8.0)
        
    Returns:
        Dictionary of ICF metrics
    """
    import math
    
    # Initialize metrics dictionary
    icf_metrics = {}
    
    # Include assumptions and parameters used in calculations
    icf_metrics['assumptions'] = {
        'wall_height_feet': f"{wall_height:.1f}",
        'standard_icf_form_width_inches': "16",
        'standard_icf_form_height_inches': "48",
        'rebar_horizontal_courses': 3,
        'rebar_vertical_spacing_inches': 24
    }
    
    # Total linear feet
    total_linear_feet = 0
    for wall in perimeter_model['walls']:
        # Convert from feet-inches format to decimal feet
        inches = feet_inches_to_inches(wall['length'])
        if inches:
            total_linear_feet += inches / 12.0
    
    icf_metrics['total_linear_feet'] = f"{total_linear_feet:.1f}"
    
    # Total number of corners
    icf_metrics['total_corners'] = len(perimeter_model['corners'])
    
    # Wall area (assuming standard height)
    wall_area_sqft = total_linear_feet * wall_height
    icf_metrics['wall_area_sqft'] = f"{wall_area_sqft:.1f}"
    
    # Wall thickness in feet (for volume calculation)
    wall_thickness_inches = 8  # Default
    if 'wall_thickness' in perimeter_model:
        try:
            # Extract numeric value from wall thickness string (e.g., "8\"")
            wall_thickness_str = perimeter_model['wall_thickness'].replace('"', '').replace('\\', '')
            wall_thickness_inches = int(wall_thickness_str)
        except (ValueError, AttributeError):
            pass
    
    wall_thickness_feet = wall_thickness_inches / 12.0
    icf_metrics['wall_thickness_feet'] = f"{wall_thickness_feet:.2f}"
    
    # Concrete volume (cubic yards)
    concrete_volume_cuft = total_linear_feet * wall_height * wall_thickness_feet
    concrete_volume_cuyd = concrete_volume_cuft / 27.0  # Convert to cubic yards
    icf_metrics['concrete_volume_cuyd'] = f"{concrete_volume_cuyd:.1f}"
    
    # Calculate bounding box
    x_coords = [corner['x'] for corner in perimeter_model['corners']]
    y_coords = [corner['y'] for corner in perimeter_model['corners']]
    width_pixels = max(x_coords) - min(x_coords)
    length_pixels = max(y_coords) - min(y_coords)
    
    # Find the scale factor (inches per pixel)
    # We can use the longest wall for this calculation
    longest_wall = max(perimeter_model['walls'], key=lambda w: w['length_pixels'])
    scale_factor_inches_per_pixel = feet_inches_to_inches(longest_wall['length']) / longest_wall['length_pixels']
    
    # Convert to feet
    width_feet = (width_pixels * scale_factor_inches_per_pixel) / 12.0
    length_feet = (length_pixels * scale_factor_inches_per_pixel) / 12.0
    
    icf_metrics['bounding_box'] = {
        'width_feet': f"{width_feet:.1f}",
        'length_feet': f"{length_feet:.1f}"
    }
    
    return icf_metrics

def process_foundation_plan(image_path: str, overall_width: str, output_dir: str = "outputs", 
                           show_steps: bool = False) -> Tuple[Dict[str, Any], np.ndarray]:
    """
    Process a foundation plan to extract perimeter walls and calculate dimensions.
    
    Args:
        image_path: Path to the foundation plan image.
        overall_width: Overall width of the foundation (e.g., "55'-0\"").
        output_dir: Output directory for result images.
        show_steps: Whether to save intermediate steps.
        
    Returns:
        perimeter_model: Foundation perimeter model with corners and walls.
        result_image: Visualization of the perimeter.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not open image {image_path}")
        # Return empty dict and blank image instead of None
        return {}, np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Convert overall width to inches
    overall_width_inches = feet_inches_to_inches(overall_width)
    if overall_width_inches is None:
        print("Error: Invalid overall width format.")
        # Return empty dict and blank image instead of None
        return {}, np.zeros((100, 100, 3), dtype=np.uint8)
    
    print(f"Overall width: {overall_width} ({overall_width_inches} inches)")
    
    # Extract perimeter walls
    print("Extracting perimeter walls...")
    perimeter_mask, geometry_data, debug_image = extract_perimeter_walls(image_path, show_steps)
    
    print(f"Detected {len(geometry_data['corners'])} corners")
    print(f"Detected {len(geometry_data['walls'])} wall segments")
    
    # Save the debug image
    if show_steps:
        debug_path = os.path.join(output_dir, "perimeter_debug.png")
        cv2.imwrite(debug_path, debug_image)
        print(f"Debug image saved to {debug_path}")
    
    # Find the longest wall segment in pixels
    longest_wall_idx = 0
    longest_wall_length = 0
    for i, wall in enumerate(geometry_data['walls']):
        if wall['length_pixels'] > longest_wall_length:
            longest_wall_length = wall['length_pixels']
            longest_wall_idx = i
    
    print(f"Longest wall is wall {longest_wall_idx + 1} at {longest_wall_length:.1f} pixels")
    
    # Calculate scale factor based on the longest wall
    # This ensures the longest wall matches the specified overall width
    scale_factor = overall_width_inches / longest_wall_length
    print(f"Scale factor: {scale_factor:.4f} inches per pixel")
    
    # Create perimeter model (in this case, our geometry_data already is the perimeter model)
    perimeter_model = geometry_data
    
    # Calculate wall lengths
    wall_lengths = calculate_wall_lengths(perimeter_model, scale_factor)
    
    # Print wall lengths
    print("\nWall Lengths:")
    for wall in perimeter_model['walls']:
        print(f"Wall {wall['id']}: {wall['length']} (from corner {wall['start_corner_id']} to {wall['end_corner_id']})")
    
    # Create a clean, positive representation of the foundation walls
    # Create a clean white background
    clean_positive_image = np.ones((image.shape[0], image.shape[1], 3), dtype=np.uint8) * 255
    
    # Draw the foundation walls in black
    for wall in perimeter_model['walls']:
        start_point = (wall['start_x'], wall['start_y'])
        end_point = (wall['end_x'], wall['end_y'])
        cv2.line(clean_positive_image, start_point, end_point, (0, 0, 0), thickness=10)  # Thick black lines
    
    # Draw corner markers in a distinct color
    for corner in perimeter_model['corners']:
        cv2.circle(clean_positive_image, (corner['x'], corner['y']), 8, (0, 0, 255), -1)  # Red dots for corners
        # Add corner IDs
        cv2.putText(clean_positive_image, str(corner['id']), (corner['x'] + 10, corner['y'] + 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    if show_steps:
        cv2.imwrite(os.path.join(output_dir, "perimeter_clean_foundation.png"), clean_positive_image)
    
    # Visualize the perimeter
    result_image = visualize_icf_perimeter(image, perimeter_model)
    
    # Save the result
    result_path = os.path.join(output_dir, "perimeter_walls.png")
    cv2.imwrite(result_path, result_image)
    print(f"Perimeter wall visualization saved to {result_path}")
    
    # Calculate ICF metrics
    icf_metrics = calculate_icf_metrics(perimeter_model)
    perimeter_model['icf_metrics'] = icf_metrics
    print("\nICF Metrics:")
    print(f"Total Linear Feet: {icf_metrics['total_linear_feet']} ft")
    print(f"Total Corners: {icf_metrics['total_corners']}")
    print(f"Wall Area: {icf_metrics['wall_area_sqft']} sq ft")
    print(f"Concrete Volume: {icf_metrics['concrete_volume_cuyd']} cu yd")
    print(f"Bounding Box: {icf_metrics['bounding_box']['width_feet']} ft × {icf_metrics['bounding_box']['length_feet']} ft")
    
    # Save the perimeter model
    perimeter_model_path = os.path.join(output_dir, "perimeter_walls.json")
    with open(perimeter_model_path, 'w') as f:
        json.dump(perimeter_model, f, indent=2)
    print(f"Perimeter wall model saved to {perimeter_model_path}")
    
    return perimeter_model, result_image

def main():
    parser = argparse.ArgumentParser(description="Extract perimeter walls from a foundation plan.")
    parser.add_argument("image_path", help="Path to the foundation plan image.")
    parser.add_argument("--overall_width", type=str,
                        help="Overall width (e.g., '55\\' -0\"'). If not provided and --use_llm is set, will be extracted using LLM.")
    parser.add_argument("--use_llm", action="store_true",
                        help="Use LLM to extract dimensions from the drawing.")
    parser.add_argument("--llm_type", default="openai", choices=["openai", "claude"],
                        help="Type of LLM to use (default: openai).")
    parser.add_argument("--show_steps", action="store_true",
                        help="Show intermediate preprocessing steps.")
    parser.add_argument("--output_dir", default="outputs",
                        help="Output directory for result images (default: outputs).")
    parser.add_argument("--no_visualize", action="store_true",
                        help="Don't display the final visualization.")
    parser.add_argument("--export_db", action="store_true",
                        help="Export results in database-ready format.")
    parser.add_argument("--project_id", type=str,
                        help="Project identifier for database export.")
    parser.add_argument("--drawing_name", type=str,
                        help="Drawing name for database export (defaults to image filename).")
    args = parser.parse_args()
    
    # Check if we need to use LLM for dimension extraction
    wall_thickness = None
    if args.use_llm:
        # Import the LLM module here to avoid circular imports
        from llm_module import extract_dimensions_with_llm, validate_dimensions
        
        print("Extracting dimensions using LLM...")
        dimensions = extract_dimensions_with_llm(args.image_path, llm_type=args.llm_type)
        
        if "error" in dimensions:
            print(f"Error extracting dimensions: {dimensions['error']}")
        else:
            # Validate the extracted dimensions
            is_valid, validation_message, validated_dimensions = validate_dimensions(dimensions, args.image_path)
            
            if not is_valid:
                print(f"Validation failed: {validation_message}")
                print("LLM explanation: " + dimensions.get("explanation", "No explanation provided"))
                
                # Check if we're running in non-interactive mode
                non_interactive = os.environ.get("NON_INTERACTIVE", "").lower() in ("true", "1", "yes")
                
                # If overall width wasn't provided as an argument
                if not args.overall_width:
                    if non_interactive:
                        # In non-interactive mode, use fallback value from environment
                        default_width = os.environ.get("DEFAULT_OVERALL_WIDTH")
                        if default_width:
                            print(f"\nUsing fallback overall width from environment: {default_width}")
                            args.overall_width = default_width
                        else:
                            print("\nError: No fallback overall width available in non-interactive mode.")
                            print("Set DEFAULT_OVERALL_WIDTH in your .env file.")
                            return
                    else:
                        # In interactive mode, prompt the user
                        print("\nThe overall width is required to process the foundation plan.")
                        user_width = input("Please enter the overall width (e.g., 38'-0\"): ")
                        if user_width:
                            args.overall_width = user_width
                        else:
                            print("No overall width provided. Exiting.")
                            return
                
                # If wall thickness wasn't identified, check for fallback
                if not wall_thickness and non_interactive:
                    default_thickness = os.environ.get("DEFAULT_WALL_THICKNESS")
                    if default_thickness:
                        print(f"Using fallback wall thickness from environment: {default_thickness}")
                        wall_thickness = default_thickness
            else:
                print(f"Validation passed: {validation_message}")
                # Handle overall width
                if validated_dimensions.get("overall_width") is not None:
                    # Use LLM-extracted overall width if not provided as argument
                    if not args.overall_width:
                        args.overall_width = validated_dimensions.get("overall_width")
                        print(f"Using LLM-extracted overall width: {args.overall_width} (Confidence: {validated_dimensions.get('confidence')}%)")
                
                # Store wall thickness for inclusion in final output
                wall_thickness = validated_dimensions.get("wall_thickness")
                if wall_thickness:
                    print(f"Wall thickness: {wall_thickness}")
                else:
                    print("Wall thickness could not be identified.")
    
    # Ensure we have an overall width
    if not args.overall_width:
        print("Error: Overall width is required. Provide it with --overall_width or use --use_llm.")
        return
    
    # Process the foundation plan
    try:
        perimeter_model, result_image = process_foundation_plan(
            args.image_path,
            args.overall_width,
            args.output_dir,
            args.show_steps
        )
        
        # Add wall thickness to the perimeter model if available
        if wall_thickness:
            perimeter_model["wall_thickness"] = wall_thickness
            
            # Update the JSON file with the new model
            perimeter_model_path = os.path.join(args.output_dir, "perimeter_walls.json")
            with open(perimeter_model_path, 'w') as f:
                json.dump(perimeter_model, f, indent=2)
            print(f"Added wall thickness ({wall_thickness}) to the perimeter model")
        
        # Export database-ready format if requested
        if args.export_db:
            try:
                # Create database output directory
                db_output_dir = os.path.join(args.output_dir, "database")
                os.makedirs(db_output_dir, exist_ok=True)
                
                # Get drawing name from image path if not provided
                drawing_name = args.drawing_name
                if not drawing_name:
                    drawing_name = Path(args.image_path).stem
                
                print(f"\nExporting database-ready format for drawing: {drawing_name}")
                
                # Prepare data for database
                db_ready_data = prepare_for_database(
                    perimeter_model,
                    drawing_name=drawing_name,
                    project_id=args.project_id
                )
                
                # Save database-ready JSON
                db_ready_path = os.path.join(db_output_dir, f"{drawing_name}_db_ready.json")
                save_database_ready_json(db_ready_data, db_ready_path)
                
                # Generate PostgreSQL statements
                sql_statements = generate_postgresql_statements(db_ready_data)
                
                # Save SQL statements
                sql_path = os.path.join(db_output_dir, f"{drawing_name}_postgresql.sql")
                with open(sql_path, 'w') as f:
                    for table, sql in sql_statements.items():
                        f.write(f"-- {table.upper()} TABLE\n")
                        f.write(sql)
                        f.write("\n\n")
                print(f"PostgreSQL statements saved to {sql_path}")
                
                # Generate Supabase payload
                supabase_payload = generate_supabase_payload(db_ready_data)
                
                # Save Supabase payload
                supabase_path = os.path.join(db_output_dir, f"{drawing_name}_supabase.json")
                with open(supabase_path, 'w') as f:
                    json.dump(supabase_payload, f, indent=2)
                print(f"Supabase payload saved to {supabase_path}")
                
                print("\nDatabase export completed successfully.")
                print("See docs/database_integration.md for information on database integration.")
                
            except NameError:
                print("\nError: Database utilities not available.")
                print("Make sure the database_utils.py module is in the same directory as this script.")
                print("See docs/database_integration.md for more information.")
            except Exception as e:
                print(f"\nError exporting database-ready format: {e}")
        
        # Display the result
        if not args.no_visualize and result_image is not None:
            # Check if we're running in a non-interactive environment
            non_interactive = os.environ.get("NON_INTERACTIVE", "").lower() in ("true", "1", "yes")
            
            if non_interactive:
                # Save the visualization instead of displaying it
                vis_path = os.path.join(args.output_dir, "perimeter_visualization.png")
                plt.figure(figsize=(12, 8))
                plt.imshow(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
                plt.title("Foundation Perimeter Walls")
                plt.axis('off')
                plt.savefig(vis_path)
                plt.close()
                print(f"Visualization saved to {vis_path} (non-interactive mode)")
            else:
                # Display the visualization in interactive mode
                plt.figure(figsize=(12, 8))
                plt.imshow(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
                plt.title("Foundation Perimeter Walls")
                plt.axis('off')
                plt.show(block=True)  # Explicitly set block=True for clarity
    except Exception as e:
        print(f"Error processing foundation plan: {e}")

if __name__ == "__main__":
    main()
