#!/usr/bin/env python3
"""
Vision-Only Extractor

This script demonstrates how to use the vision module to detect corners and walls
without using an LLM. It's a simpler approach that relies solely on computer vision.

Usage:
    python vision_only_extractor.py <image_path> --overall_width <width>

Example:
    python vision_only_extractor.py src/Screenshot.png --overall_width "55'-0\""
"""

import os
import argparse
import cv2
import numpy as np
import matplotlib.pyplot as plt

# Import only vision module functions
from vision_module import (
    preprocess_image_for_walls,
    get_overall_dimension_pixels,
    feet_inches_to_inches,
    calculate_scale_factor,
    get_wall_segment_lengths_pixels,
    convert_to_real_world,
    visualize_results
)

def extract_with_vision_only(image_path, overall_width, output_dir="outputs", show_steps=False):
    """
    Extract foundation walls using only computer vision techniques.
    
    Args:
        image_path: Path to the foundation plan image.
        overall_width: Overall width of the foundation (e.g., "55'-0\"").
        output_dir: Output directory for result images.
        show_steps: Whether to save intermediate steps.
        
    Returns:
        result_image: Visualization of the detected walls.
        wall_lengths: Dictionary of wall lengths.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not open image {image_path}")
        return None, None
    
    # Convert overall width to inches
    overall_width_inches = feet_inches_to_inches(overall_width)
    if overall_width_inches is None:
        print("Error: Invalid overall width format.")
        return None, None
    
    print(f"Overall width: {overall_width} ({overall_width_inches} inches)")
    
    # Step 1: Preprocess image to detect walls
    print("Detecting walls...")
    wall_image, filtered_contours, geometry_data = preprocess_image_for_walls(image_path, show_steps)
    
    print(f"Detected {len(geometry_data['corners'])} corners")
    print(f"Detected {len(geometry_data['walls'])} wall segments")
    
    # Step 2: Calculate overall dimension in pixels
    overall_width_pixels = get_overall_dimension_pixels(wall_image, "horizontal")
    print(f"Overall width in pixels: {overall_width_pixels}")
    
    # Step 3: Calculate scale factor
    scale_factor = calculate_scale_factor(overall_width_inches, overall_width_pixels)
    print(f"Scale factor: {scale_factor:.4f} inches per pixel")
    
    # Step 4: Get wall segment lengths in pixels
    segment_lengths_pixels = get_wall_segment_lengths_pixels(filtered_contours)
    
    # Step 5: Convert to real-world dimensions
    segment_lengths_real = convert_to_real_world(segment_lengths_pixels, scale_factor)
    
    # Step 6: Format wall lengths for visualization
    wall_lengths = {}
    for i, length in enumerate(segment_lengths_real):
        feet = int(length // 12)
        inches = int(round(length % 12))
        wall_lengths[f"Wall {i+1}"] = f"{feet}'-{inches}\""
        print(f"Wall {i+1}: {feet}'-{inches}\"")
    
    # Step 7: Visualize the results
    result_image = visualize_results(image, wall_lengths, [], filtered_contours, geometry_data)
    
    # Save the result
    result_path = os.path.join(output_dir, "vision_only_result.png")
    cv2.imwrite(result_path, result_image)
    print(f"Result saved to {result_path}")
    
    return result_image, wall_lengths

def main():
    parser = argparse.ArgumentParser(description="Extract foundation walls using only computer vision.")
    parser.add_argument("image_path", help="Path to the foundation plan image.")
    parser.add_argument("--overall_width", type=str, required=True,
                        help="Overall width (e.g., '55\\' -0\"').")
    parser.add_argument("--show_steps", action="store_true",
                        help="Show intermediate preprocessing steps.")
    parser.add_argument("--output_dir", default="outputs",
                        help="Output directory for result images (default: outputs).")
    parser.add_argument("--no_visualize", action="store_true",
                        help="Don't display the final visualization.")
    args = parser.parse_args()
    
    # Extract walls
    result_image, wall_lengths = extract_with_vision_only(
        args.image_path,
        args.overall_width,
        args.output_dir,
        args.show_steps
    )
    
    # Display the result
    if not args.no_visualize and result_image is not None:
        plt.figure(figsize=(12, 8))
        plt.imshow(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
        plt.title("Foundation Wall Analysis (Vision Only)")
        plt.axis('off')
        plt.show()

if __name__ == "__main__":
    main()
