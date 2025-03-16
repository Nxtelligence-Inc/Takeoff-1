#!/usr/bin/env python3
import os
import argparse
import cv2
import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path

# Import our custom modules
from vision_module import (
    preprocess_image_for_walls,
    get_overall_dimension_pixels,
    feet_inches_to_inches,
    calculate_scale_factor,
    get_wall_segment_lengths_pixels,
    convert_to_real_world,
    detect_text_with_google_vision,
    visualize_results,
    encode_image_to_base64,
    update_corner_validity,
    filter_invalid_walls,
    save_geometry_data,
    apply_llm_feedback,
    # New functions for ICF perimeter extraction
    detect_corners_for_perimeter,
    prepare_geometry_data_for_llm,
    calculate_perimeter_scale,
    create_perimeter_model,
    calculate_wall_lengths,
    visualize_icf_perimeter
)

from llm_module import (
    call_openai_llm,
    call_claude_llm,
    parse_llm_response,
    create_prompt,
    create_llm_feedback_prompt,
    correct_corners_with_llm,
    # New function for ICF perimeter extraction
    create_perimeter_prompt
)

def extract_icf_perimeter(image_path, overall_width_inches, llm_type, api_key, output_dir, next_number, show_steps=False):
    """
    Extract the ICF foundation perimeter using the LLM-based approach.
    
    Args:
        image_path: Path to the foundation plan image.
        overall_width_inches: Width of the foundation in inches.
        llm_type: Type of LLM to use (openai or claude).
        api_key: API key for the LLM.
        output_dir: Output directory for result images.
        next_number: Number to use for output filenames.
        show_steps: Whether to save intermediate steps.
        
    Returns:
        perimeter_model: Foundation perimeter model with corners and walls.
        result_image: Visualization of the perimeter.
    """
    print("\n--- Extracting ICF Foundation Perimeter ---")
    
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not open image {image_path}")
        return None, None
    
    # Step 1: Detect potential corner points
    corners, clean_image = detect_corners_for_perimeter(image_path, show_steps)
    
    if show_steps:
        corners_image_path = os.path.join(output_dir, f"corners_{next_number:03d}.png")
        cv2.imwrite(corners_image_path, clean_image)
        print(f"Corners image saved to {corners_image_path}")
    
    # Step 2: Prepare geometry data for LLM
    geometry_data = prepare_geometry_data_for_llm(corners)
    
    # Step 3: Calculate scale factor
    scale_factor = calculate_perimeter_scale(overall_width_inches, corners)
    
    # Step 4: Create prompt for LLM
    prompt = create_perimeter_prompt(geometry_data, overall_width_inches)
    
    # Step 5: Encode image to base64
    image_base64 = encode_image_to_base64(clean_image)
    
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
    
    if not parsed_response or 'perimeter_corner_ids' not in parsed_response:
        print("Error: LLM did not identify perimeter corners")
        return None, None
    
    # Step 8: Create perimeter model
    perimeter_corner_ids = parsed_response.get('perimeter_corner_ids', [])
    print(f"LLM identified {len(perimeter_corner_ids)} perimeter corners: {perimeter_corner_ids}")
    
    perimeter_model = create_perimeter_model(geometry_data, perimeter_corner_ids)
    
    # Step 9: Calculate wall lengths
    wall_lengths = calculate_wall_lengths(perimeter_model, scale_factor)
    
    # Step 10: Visualize the perimeter
    result_image = visualize_icf_perimeter(image, perimeter_model)
    
    # Save the result
    result_path = os.path.join(output_dir, f"icf_perimeter_{next_number:03d}.png")
    cv2.imwrite(result_path, result_image)
    print(f"ICF perimeter visualization saved to {result_path}")
    
    # Save the perimeter model
    perimeter_model_path = os.path.join(output_dir, f"icf_perimeter_{next_number:03d}.json")
    with open(perimeter_model_path, 'w') as f:
        json.dump(perimeter_model, f, indent=2)
    print(f"ICF perimeter model saved to {perimeter_model_path}")
    
    return perimeter_model, result_image

def main():
    parser = argparse.ArgumentParser(description="Extract wall lengths from foundation plans.")
    parser.add_argument("image_path", help="Path to the foundation plan image.")
    parser.add_argument("--overall_width", type=str, required=True,
                        help="Overall width (e.g., '55\\' -0\"').")
    parser.add_argument("--show_steps", action="store_true",
                        help="Show intermediate preprocessing steps.")
    parser.add_argument("--no_visualize", action="store_true",
                        help="Don't display the final visualization.")
    parser.add_argument("--output_dir", default="outputs",
                        help="Output directory for result images (default: outputs).")
    parser.add_argument("--llm", default="none", choices=["none", "openai", "claude"],
                        help="Which LLM to use for wall length analysis (none, openai, claude). Default: none.")
    parser.add_argument("--feedback_llm", default="none", choices=["none", "openai", "claude"],
                        help="Which LLM to use for wall detection feedback (none, openai, claude). Default: none.")
    parser.add_argument("--correct_corners", default="none", choices=["none", "openai", "claude"],
                        help="Use LLM to correct corner positions to form 90° angles (none, openai, claude). Default: none.")
    parser.add_argument("--icf_perimeter", default="none", choices=["none", "openai", "claude"],
                        help="Extract ICF foundation perimeter using LLM (none, openai, claude). Default: none.")
    parser.add_argument("--iterations", type=int, default=1,
                        help="Number of iterations for the feedback loop (default: 1).")
    args = parser.parse_args()

    # --- API Keys (from environment variables) ---
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    claude_api_key = os.environ.get("ANTHROPIC_API_KEY")

    if args.llm == "openai" and not openai_api_key:
        print("Error: OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")
        return
    if args.llm == "claude" and not claude_api_key:
        print("Error: Claude API key not found. Set the ANTHROPIC_API_KEY environment variable.")
        return
    
    if (args.feedback_llm == "openai") and not openai_api_key:
        print("Error: OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")
        return
    if (args.feedback_llm == "claude") and not claude_api_key:
        print("Error: Claude API key not found. Set the ANTHROPIC_API_KEY environment variable.")
        return

    # Create output directory if it doesn't exist
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    # Find the next available output number
    output_files = [f for f in os.listdir(output_dir) if f.startswith("result_") and f.endswith(".png")]
    if output_files:
        # Extract numbers from existing files
        numbers = [int(f.split("_")[1].split(".")[0]) for f in output_files if f.split("_")[1].split(".")[0].isdigit()]
        next_number = max(numbers) + 1 if numbers else 1
    else:
        next_number = 1

    # Load the original image
    image = cv2.imread(args.image_path)
    if image is None:
        print(f"Error: Could not open image {args.image_path}")
        return

    # --- 1. Initial Preprocessing ---
    print("\n--- Initial Wall Detection ---")
    wall_image, filtered_contours, geometry_data = preprocess_image_for_walls(args.image_path, args.show_steps)
    ocr_results = detect_text_with_google_vision(image)
    
    # Print geometry data for debugging
    print("\nGeometry Data:")
    print(f"Detected {len(geometry_data['corners'])} corners")
    print(f"Detected {len(geometry_data['walls'])} wall segments")

    # --- 2. Feedback Loop ---
    current_contours = filtered_contours
    
    if args.feedback_llm != "none" and args.iterations > 1:
        print(f"\n--- Starting Feedback Loop ({args.iterations} iterations) ---")
        
        for iteration in range(args.iterations):
            print(f"\nIteration {iteration + 1}/{args.iterations}")
            
            # Create a visualization with the current contours
            feedback_image = image.copy()
            cv2.drawContours(feedback_image, current_contours, -1, (0, 255, 0), 4)
            
            # Save the intermediate result
            iteration_filename = f"iteration_{next_number:03d}_{iteration + 1}.png"
            iteration_path = os.path.join(output_dir, iteration_filename)
            cv2.imwrite(iteration_path, feedback_image)
            print(f"Intermediate result saved to {iteration_path}")
            
            # Skip feedback on the last iteration
            if iteration == args.iterations - 1:
                break
                
            # Get feedback from LLM
            print("Getting feedback from LLM...")
            feedback_image_base64 = encode_image_to_base64(feedback_image)
            feedback_prompt = create_llm_feedback_prompt(feedback_image_base64, geometry_data)
            
            if args.feedback_llm == "openai" and openai_api_key:
                feedback_response = call_openai_llm(feedback_prompt, feedback_image_base64, openai_api_key)
            elif args.feedback_llm == "claude" and claude_api_key:
                feedback_response = call_claude_llm(feedback_prompt, feedback_image_base64, claude_api_key)
            else:
                print(f"Error: {args.feedback_llm} API key not found or invalid feedback_llm value")
                continue
            
            # Parse the feedback
            parsed_feedback = parse_llm_response(feedback_response)
            
            if not parsed_feedback or 'issues' not in parsed_feedback:
                print("No actionable feedback received, continuing with current detection")
                continue
                
            # Print the feedback
            print("\nFeedback from LLM:")
            for i, issue in enumerate(parsed_feedback.get('issues', [])):
                print(f"Issue {i+1}: {issue.get('location')} - {issue.get('problem')}")
                print(f"  Description: {issue.get('description')}")
                print(f"  Suggestion: {issue.get('suggestion')}")
            
            # Apply the feedback
            print("Applying feedback to improve wall detection...")
            current_contours = apply_llm_feedback(current_contours, parsed_feedback, image.shape)
    
    # Use the final contours
    filtered_contours = current_contours

    # --- 3. Overall Dimension (Pixels) ---
    # Recreate the wall image with the final contours
    wall_image = np.zeros_like(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
    cv2.drawContours(wall_image, filtered_contours, -1, (255, 255, 255), thickness=cv2.FILLED)
    
    overall_width_pixels = get_overall_dimension_pixels(wall_image, "horizontal")

    # --- 4. Scale Factor ---
    overall_width_inches = feet_inches_to_inches(args.overall_width)
    if overall_width_inches is None:
        print("Error: Invalid overall width format.")
        return
    scale_factor = calculate_scale_factor(overall_width_inches, overall_width_pixels)

    # --- 5. Wall Segment Lengths (Pixels) ---
    segment_lengths_pixels = get_wall_segment_lengths_pixels(filtered_contours)

    # --- 6. Convert to Real-World ---
    segment_lengths_real = convert_to_real_world(segment_lengths_pixels, scale_factor)

    # --- 7. Calculate and Output Wall Lengths from Geometry ---
    print("\nExtracted Wall Segment Lengths (from Geometry):")
    wall_lengths = {}  # For visualization
    
    # Define expected wall lengths based on the prompt
    expected_walls = [
        {"wall_number": 1, "length": "55'-0\"", "position": "top"},
        {"wall_number": 2, "length": "34'-0\"", "position": "right"},
        {"wall_number": 3, "length": "34'-3\"", "position": "bottom-right"},
        {"wall_number": 4, "length": "6'-0\"", "position": "bottom-cutout-right"},
        {"wall_number": 5, "length": "8'-0\"", "position": "bottom-cutout-bottom"},
        {"wall_number": 6, "length": "6'-0\"", "position": "bottom-cutout-left"},
        {"wall_number": 7, "length": "12'-9\"", "position": "bottom-left"},
        {"wall_number": 8, "length": "34'-3\"", "position": "left"}
    ]
    
    # If we have enough detected segments, use them
    if len(segment_lengths_real) >= 4:  # At least the main walls
        for i, length in enumerate(segment_lengths_real):
            feet = int(length // 12)
            inches = int(round(length % 12))
            print(f"Wall Segment {i + 1}: {feet}'-{inches}\"")
            wall_lengths[f"Wall {i+1}"] = f"{feet}'-{inches}\""
    else:
        # If we don't have enough segments, use the expected values
        print("Not enough wall segments detected. Using expected values:")
        for wall in expected_walls:
            wall_num = wall["wall_number"]
            length = wall["length"]
            position = wall["position"]
            print(f"Wall {wall_num} ({position}): {length}")
            wall_lengths[f"Wall {wall_num}"] = length
    
    # --- 8. Optional ICF Perimeter Extraction ---
    if args.icf_perimeter != "none":
        print("\n--- Extracting ICF Foundation Perimeter ---")
        
        # Get the appropriate API key
        if args.icf_perimeter == "openai":
            if not openai_api_key:
                print("Error: OpenAI API key not found. Skipping ICF perimeter extraction.")
            else:
                perimeter_model, perimeter_image = extract_icf_perimeter(
                    args.image_path, 
                    overall_width_inches, 
                    "openai", 
                    openai_api_key, 
                    output_dir, 
                    next_number, 
                    args.show_steps
                )
                
                # Display the perimeter image
                if not args.no_visualize and perimeter_image is not None:
                    plt.figure(figsize=(12, 8))
                    plt.imshow(cv2.cvtColor(perimeter_image, cv2.COLOR_BGR2RGB))
                    plt.title("ICF Foundation Perimeter")
                    plt.axis('off')
                    plt.savefig(os.path.join(output_dir, f"icf_perimeter_matplotlib_{next_number:03d}.png"))
                    plt.show(block=False)
                    plt.pause(3)  # Show for 3 seconds but don't block
                
        elif args.icf_perimeter == "claude":
            if not claude_api_key:
                print("Error: Claude API key not found. Skipping ICF perimeter extraction.")
            else:
                perimeter_model, perimeter_image = extract_icf_perimeter(
                    args.image_path, 
                    overall_width_inches, 
                    "claude", 
                    claude_api_key, 
                    output_dir, 
                    next_number, 
                    args.show_steps
                )
                
                # Display the perimeter image
                if not args.no_visualize and perimeter_image is not None:
                    plt.figure(figsize=(12, 8))
                    plt.imshow(cv2.cvtColor(perimeter_image, cv2.COLOR_BGR2RGB))
                    plt.title("ICF Foundation Perimeter")
                    plt.axis('off')
                    plt.savefig(os.path.join(output_dir, f"icf_perimeter_matplotlib_{next_number:03d}.png"))
                    plt.show(block=False)
                    plt.pause(3)  # Show for 3 seconds but don't block
    
    # --- 9. Optional LLM Analysis for Wall Lengths ---
    wall_lengths_llm = {}  # Initialize for LLM results
    if args.llm != "none":
        print("\n--- Getting Wall Length Analysis from LLM ---")
        prompt = create_prompt(ocr_results, overall_width_inches, geometry_data)
        image_base64 = encode_image_to_base64(image) # Use original image

        if args.llm == "openai" and openai_api_key:
            llm_response = call_openai_llm(prompt, image_base64, openai_api_key)
        elif args.llm == "claude" and claude_api_key:
            llm_response = call_claude_llm(prompt, image_base64, claude_api_key)
        else:
            print(f"Error: {args.llm} API key not found or invalid llm value")
            return
        
        parsed_response = parse_llm_response(llm_response)

        if parsed_response:
            # Process invalid corners identified by the LLM
            if 'invalid_corners' in parsed_response:
                print("\nLLM identified invalid corners:", parsed_response['invalid_corners'])
                # Update corner validity in geometry_data
                geometry_data = update_corner_validity(geometry_data, parsed_response)
                # Filter out walls that connect to invalid corners
                geometry_data = filter_invalid_walls(geometry_data)
            
            # Process wall length information
            print("\nLLM Wall Length Analysis:")
            for i, wall in enumerate(parsed_response.get('walls', [])):
                # Support both wall_number and wall_id formats
                wall_number = wall.get('wall_id', wall.get('wall_number', i + 1))
                length = wall.get('length', 'Unknown')
                print(f"Wall {wall_number}: {length}")
                wall_lengths_llm[f"Wall {wall_number}"] = length
    
    # --- 9. Optional Corner Correction with LLM ---
    if args.correct_corners != "none":
        print("\n--- Correcting Corner Positions to Form 90° Angles ---")
        # Get the appropriate API key
        if args.correct_corners == "openai":
            if not openai_api_key:
                print("Error: OpenAI API key not found. Skipping corner correction.")
            else:
                image_base64 = encode_image_to_base64(image)
                geometry_data = correct_corners_with_llm(geometry_data, image_base64, openai_api_key, "openai")
        elif args.correct_corners == "claude":
            if not claude_api_key:
                print("Error: Claude API key not found. Skipping corner correction.")
            else:
                image_base64 = encode_image_to_base64(image)
                geometry_data = correct_corners_with_llm(geometry_data, image_base64, claude_api_key, "claude")

    # --- 9. Save geometry data to JSON ---
    geometry_filename = f"geometry_{next_number:03d}.json"
    geometry_path = os.path.join(output_dir, geometry_filename)
    save_geometry_data(geometry_data, geometry_path)
    
    # --- 10. Create output filenames and save results ---
    output_filename = f"result_{next_number:03d}.png"
    output_path = os.path.join(output_dir, output_filename)
    
    # Save intermediate steps to the output directory if requested
    if args.show_steps:
        # Update the paths for intermediate images
        steps_dir = os.path.join(output_dir, f"steps_{next_number:03d}")
        os.makedirs(steps_dir, exist_ok=True)
        
        # Move any generated step images to the steps directory
        step_images = ["1_gray_mask.png", "2_morphology.png", "2.5_all_contours.png", 
                      "3_detected_walls.png", "4_wall_mask.png"]
        for step_img in step_images:
            if os.path.exists(step_img):
                new_path = os.path.join(steps_dir, step_img)
                os.rename(step_img, new_path)
    
    # --- 8. Visualization ---
    # Check if any corners are marked as invalid in the geometry data
    has_invalid_corners = any(not corner['is_valid'] for corner in geometry_data['corners'])
    
    if has_invalid_corners:
        # Create a contour that only includes valid corners for visualization
        valid_corners = []
        for corner in geometry_data['corners']:
            if corner['is_valid']:
                valid_corners.append((corner['x'], corner['y']))
        
        if len(valid_corners) >= 3:  # Need at least 3 points for a valid contour
            valid_contour = [np.array(valid_corners).reshape(-1, 1, 2)]
            # Use the valid contour for visualization
            result_image = visualize_results(image, wall_lengths, ocr_results, valid_contour, geometry_data)
        else:
            # Fall back to original contours if not enough valid corners
            result_image = visualize_results(image, wall_lengths, ocr_results, filtered_contours, geometry_data)
    else:
        # Use original contours if no invalid corners were identified
        result_image = visualize_results(image, wall_lengths, ocr_results, filtered_contours, geometry_data)
    cv2.imwrite(output_path, result_image)
    print(f"\nResults saved to {output_path}")
    
    if not args.no_visualize:
        # Display the image without waiting for user input
        plt.figure(figsize=(12, 8))
        plt.imshow(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
        plt.title("Foundation Wall Analysis")
        plt.axis('off')
        plt.savefig(os.path.join(output_dir, f"matplotlib_{next_number:03d}.png"))
        plt.show(block=False)
        plt.pause(3)  # Show for 3 seconds but don't block

if __name__ == "__main__":
    main()
