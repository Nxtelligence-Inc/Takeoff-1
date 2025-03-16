#!/usr/bin/env python3
"""
Unified Foundation Extractor

This script provides a unified interface to extract foundation information using
different approaches:
1. Vision-only: Uses computer vision to detect walls and corners
2. ICF Perimeter: Uses vision + LLM to extract the perimeter for ICF construction
3. Full Analysis: Uses vision + LLM for wall detection, corner correction, and feedback

Usage:
    python unified_extractor.py <image_path> --overall_width <width> --mode <mode> --llm <llm_type>

Example:
    python unified_extractor.py src/Screenshot.png --overall_width "55'-0\"" --mode icf --llm claude
"""

import os
import argparse
import cv2
import matplotlib.pyplot as plt

# Import the extraction functions from the other scripts
from vision_only_extractor import extract_with_vision_only
from icf_perimeter_extractor import extract_perimeter

def main():
    parser = argparse.ArgumentParser(description="Unified foundation extractor.")
    parser.add_argument("image_path", help="Path to the foundation plan image.")
    parser.add_argument("--overall_width", type=str, required=True,
                        help="Overall width (e.g., '55\\' -0\"').")
    parser.add_argument("--mode", choices=["vision", "icf", "full"], required=True,
                        help="Extraction mode: vision-only, ICF perimeter, or full analysis.")
    parser.add_argument("--llm", choices=["openai", "claude"], 
                        help="Which LLM to use (required for icf and full modes).")
    parser.add_argument("--show_steps", action="store_true",
                        help="Show intermediate preprocessing steps.")
    parser.add_argument("--output_dir", default="outputs",
                        help="Output directory for result images (default: outputs).")
    parser.add_argument("--no_visualize", action="store_true",
                        help="Don't display the final visualization.")
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Check if image exists
    if not os.path.exists(args.image_path):
        print(f"Error: Image file not found: {args.image_path}")
        return
    
    # Check if LLM is specified for modes that require it
    if args.mode in ["icf", "full"] and not args.llm:
        print(f"Error: --llm argument is required for {args.mode} mode")
        return
    
    # Get API key from environment variables if needed
    api_key = None
    if args.mode in ["icf", "full"] and args.llm:
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
    
    # Process based on the selected mode
    if args.mode == "vision":
        print("\n=== Running Vision-Only Extraction ===\n")
        result_image, wall_lengths = extract_with_vision_only(
            args.image_path,
            args.overall_width,
            args.output_dir,
            args.show_steps
        )
        
        title = "Foundation Wall Analysis (Vision Only)"
        
    elif args.mode == "icf":
        print("\n=== Running ICF Perimeter Extraction ===\n")
        perimeter_model, result_image = extract_perimeter(
            args.image_path,
            args.overall_width,
            args.llm,
            api_key,
            args.output_dir,
            args.show_steps
        )
        
        title = "ICF Foundation Perimeter"
        
    elif args.mode == "full":
        print("\n=== Running Full Foundation Analysis ===\n")
        print("This mode uses the foundation_extractor.py script.")
        print("Please run it directly with the appropriate arguments:")
        print(f"python src/foundation_extractor.py {args.image_path} --overall_width \"{args.overall_width}\" --llm {args.llm} --icf_perimeter {args.llm} --correct_corners {args.llm}")
        return
    
    # Display the result
    if not args.no_visualize and 'result_image' in locals() and result_image is not None:
        plt.figure(figsize=(12, 8))
        plt.imshow(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
        plt.title(title)
        plt.axis('off')
        plt.show()

if __name__ == "__main__":
    main()
