#!/usr/bin/env python3
"""
ICF Perimeter Extractor

This script extracts the perimeter of a foundation plan for ICF construction.
It uses computer vision to detect potential corner points and an LLM to identify
the actual perimeter corners.

Usage:
    python icf_perimeter_extractor.py <image_path> --overall_width <width> --llm <llm_type>

Example:
    python icf_perimeter_extractor.py src/Screenshot.png --overall_width "55'-0\"" --llm claude
"""

import os
import argparse
import cv2
import numpy as np
import matplotlib.pyplot as plt
import json

# Import vision module functions
from vision_module import (
    preprocess_image_for_walls,
    prepare_geometry_data_for_llm,
    create_perimeter_model,
    calculate_wall_lengths,
    visualize_icf_perimeter,
    encode_image_to_base64,
    feet_inches_to_inches,
    get_overall_dimension_pixels,
    calculate_scale_factor
)

# Import LLM module functions
from llm_module import (
    call_openai_llm,
    call_claude_llm,
    create_perimeter_prompt,
    parse_llm_response
)

def extract_perimeter(image_path, overall_width, llm_type, api_key, output_dir="outputs", show_steps=False):
    """
    Extract the foundation perimeter for ICF construction.
    
    Args:
        image_path: Path to the foundation plan image.
        overall_width: Overall width of the foundation (e.g., "55'-0\"").
        llm_type: Type of LLM to use (openai or claude).
        api_key: API key for the LLM.
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
        return None, None
    
    # Convert overall width to inches
    overall_width_inches = feet_inches_to_inches(overall_width)
    if overall_width_inches is None:
        print("Error: Invalid overall width format.")
        return None, None
    
    print(f"Overall width: {overall_width} ({overall_width_inches} inches)")
    
    # Step 1: Preprocess image to detect walls and corners
    print("Detecting walls and corners...")
    wall_image, filtered_contours, geometry_data = preprocess_image_for_walls(image_path, show_steps)
    
    print(f"Detected {len(geometry_data['corners'])} corners")
    print(f"Detected {len(geometry_data['walls'])} wall segments")
    
    # Create a clean image with the detected corners for LLM analysis
    clean_image = image.copy()
    for corner in geometry_data['corners']:
        # Draw a clearly visible marker for each corner
        cv2.circle(clean_image, (corner['x'], corner['y']), 8, (0, 0, 255), -1)  # RED dot
        cv2.circle(clean_image, (corner['x'], corner['y']), 8, (0, 0, 0), 2)     # Black outline
        
        # Add ID number near the point with better visibility
        text_x = corner['x'] + 10
        text_y = corner['y'] + 5
        # Draw white background for better contrast
        cv2.putText(clean_image, str(corner['id']), (text_x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 5)  # White background/outline
        # Draw text in black
        cv2.putText(clean_image, str(corner['id']), (text_x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)        # Black text
    
    if show_steps:
        corners_path = os.path.join(output_dir, "corners.png")
        cv2.imwrite(corners_path, clean_image)
        print(f"Corners image saved to {corners_path}")
    
    # Step 2: Calculate overall dimension in pixels
    overall_width_pixels = get_overall_dimension_pixels(wall_image, "horizontal")
    print(f"Overall width in pixels: {overall_width_pixels}")
    
    # Step 3: Calculate scale factor
    scale_factor = calculate_scale_factor(overall_width_inches, overall_width_pixels)
    print(f"Scale factor: {scale_factor:.4f} inches per pixel")
    
    # Step 4: Create prompt for LLM
    prompt = create_perimeter_prompt(geometry_data, overall_width_inches)
    
    # Resize and encode image to base64
    # Resize image to reduce size before sending to LLM (max 800px dimension to stay well under Claude's limit)
    from vision_module import resize_image_for_vision_api
    resized_image = resize_image_for_vision_api(clean_image, max_dim=800)
    image_base64 = encode_image_to_base64(resized_image)
    
    # Step 6: Call the LLM
    print(f"Sending image to {llm_type} for perimeter analysis...")
    if llm_type == "openai":
        llm_response = call_openai_llm(prompt, image_base64, api_key)
    elif llm_type == "claude":
        llm_response = call_claude_llm(prompt, image_base64, api_key)
    else:
        print(f"Error: Unsupported LLM type: {llm_type}")
        return None, None
    
    # Step 7: Parse the LLM response
    parsed_response = parse_llm_response(llm_response)
    
    if not parsed_response:
        print("Error: Could not parse LLM response")
        return None, None
        
    if 'perimeter_corner_ids' not in parsed_response:
        print("Error: LLM did not identify perimeter corners")
        print("LLM response:", json.dumps(parsed_response, indent=2))
        return None, None
    
    # Step 8: Create perimeter model
    # At this point, we know parsed_response is not None and contains 'perimeter_corner_ids'
    perimeter_corner_ids = parsed_response['perimeter_corner_ids']
    print(f"LLM identified {len(perimeter_corner_ids)} perimeter corners: {perimeter_corner_ids}")
    
    # Print explanation if available
    explanation = parsed_response.get('explanation')
    if explanation:
        print(f"LLM explanation: {explanation}")
    
    # Create perimeter model
    try:
        perimeter_model = create_perimeter_model(geometry_data, perimeter_corner_ids)
        if perimeter_model is None:
            print("Error: Failed to create perimeter model")
            return None, None
    except Exception as e:
        print(f"Error creating perimeter model: {e}")
        return None, None
    
    # Step 9: Calculate wall lengths
    try:
        wall_lengths = calculate_wall_lengths(perimeter_model, scale_factor)
    except Exception as e:
        print(f"Error calculating wall lengths: {e}")
        return None, None
    
    # Print wall lengths
    print("\nWall Lengths:")
    for wall in perimeter_model['walls']:
        print(f"Wall {wall['id']}: {wall['length']} (from corner {wall['start_corner_id']} to {wall['end_corner_id']})")
    
    # Step 10: Create a clean, positive representation of the foundation walls
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
        cv2.imwrite(os.path.join(output_dir, "clean_foundation_for_vision.png"), clean_positive_image)
    
    # Step 11: Visualize the perimeter
    result_image = visualize_icf_perimeter(image, perimeter_model)
    
    # Save the result
    result_path = os.path.join(output_dir, "icf_perimeter.png")
    cv2.imwrite(result_path, result_image)
    print(f"ICF perimeter visualization saved to {result_path}")
    
    # Save the perimeter model
    perimeter_model_path = os.path.join(output_dir, "icf_perimeter.json")
    with open(perimeter_model_path, 'w') as f:
        json.dump(perimeter_model, f, indent=2)
    print(f"ICF perimeter model saved to {perimeter_model_path}")
    
    return perimeter_model, result_image

def main():
    parser = argparse.ArgumentParser(description="Extract foundation perimeter for ICF construction.")
    parser.add_argument("image_path", help="Path to the foundation plan image.")
    parser.add_argument("--overall_width", type=str, required=True,
                        help="Overall width (e.g., '55\\' -0\"').")
    parser.add_argument("--llm", choices=["openai", "claude"], required=True,
                        help="Which LLM to use for perimeter analysis (openai or claude).")
    parser.add_argument("--show_steps", action="store_true",
                        help="Show intermediate preprocessing steps.")
    parser.add_argument("--output_dir", default="outputs",
                        help="Output directory for result images (default: outputs).")
    parser.add_argument("--no_visualize", action="store_true",
                        help="Don't display the final visualization.")
    args = parser.parse_args()
    
    # Get API key from environment variables
    api_key = None
    if args.llm == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Error: OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")
            return
    elif args.llm == "claude":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: Claude API key not found. Set the ANTHROPIC_API_KEY environment variable.")
            return
    
    # Extract perimeter
    perimeter_model, result_image = extract_perimeter(
        args.image_path,
        args.overall_width,
        args.llm,
        api_key,
        args.output_dir,
        args.show_steps
    )
    
    # Display the result
    if not args.no_visualize and result_image is not None:
        plt.figure(figsize=(12, 8))
        plt.imshow(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
        plt.title("ICF Foundation Perimeter")
        plt.axis('off')
        plt.show()

if __name__ == "__main__":
    main()
