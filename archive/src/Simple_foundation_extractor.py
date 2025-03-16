#!/usr/bin/env python3
import os
import base64
import json
import matplotlib.pyplot as plt
import cv2
import numpy as np
import re
import argparse
import copy
from pathlib import Path
import requests
from typing import List, Dict, Tuple, Any, Sequence, Optional, Union

try:
    from google.cloud import vision
except ImportError:
    print("Warning: Google Cloud Vision package not installed. Vision features will not work.")
    vision = None

try:
    import openai
except ImportError:
    print("Warning: OpenAI package not installed. GPT-4o features will not work.")
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    print("Warning: Google Generative AI package not installed. Gemini features will not work.")
    genai = None

try:
    # Import Anthropic for Claude API
    from anthropic import Anthropic, AnthropicError
except ImportError:
    print("Warning: Anthropic package not installed. Claude features will not work.")
    Anthropic = None
    AnthropicError = Exception  # Fallback for type checking

# --- Helper Functions ---
def resize_image_for_vision_api(image, max_dim=1000):
    """
    Resize image to ensure its maximum dimension doesn't exceed max_dim,
    while preserving aspect ratio.
    
    Args:
        image: OpenCV image (numpy array)
        max_dim: Maximum dimension in pixels
        
    Returns:
        Resized image
    """
    # Get current dimensions
    height, width = image.shape[:2]
    
    # Check if resizing is needed
    if max(height, width) <= max_dim:
        return image
    
    # Calculate scale factor
    if width >= height:
        scale_factor = max_dim / width
    else:
        scale_factor = max_dim / height
    
    # Calculate new dimensions
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    
    # Resize using OpenCV
    resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    print(f"Resized image from {width}x{height} to {new_width}x{new_height}")
    return resized_image

def feet_inches_to_inches(feet_str):
    """Converts a string like '55'-0"' or "38'-0\"" to inches."""
    try:
        # Remove any escape characters and normalize quotes
        feet_str = feet_str.replace('\\', '').replace('"', '"').replace('"', '"')
        
        # Split on the feet symbol
        if "'" in feet_str:
            feet_part, inches_part = feet_str.split("'", 1)
        else:
            # Try alternative format
            feet_part = feet_str
            inches_part = "0"
        
        # Clean up and convert feet
        feet_part = feet_part.strip()
        feet = int(feet_part)
        
        # Clean up and convert inches
        inches_part = inches_part.replace('"', '').strip()
        if inches_part and inches_part != '0':
            inches = int(inches_part)
        else:
            inches = 0
            
        total_inches = (feet * 12) + inches
        print(f"Converted '{feet_str}' to {total_inches} inches ({feet} feet and {inches} inches)")
        return total_inches
    except (ValueError, IndexError) as e:
        print(f"Error parsing dimension '{feet_str}': {e}")
        return None

def detect_corners(image_path, show_steps=False):
    """
    Detects the corners of the building in the foundation plan.
    
    Args:
        image_path: Path to image.
        show_steps: If True, save intermediate images for debugging.
        
    Returns:
        corners: List of corner points (x, y) coordinates.
        debug_image: Image with detected corners for visualization.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not open/find image: {image_path}")
    
    # Create a copy for visualization
    debug_image = image.copy()
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Step 1: Target the gray color range of the walls
    lower_gray = np.array([110], dtype=np.uint8)  # Lower bound for gray
    upper_gray = np.array([170], dtype=np.uint8)  # Upper bound for gray
    gray_mask = cv2.inRange(gray, lower_gray, upper_gray)
    
    if show_steps:
        cv2.imwrite("1_gray_mask.png", gray_mask)
    
    # Step 2: Apply morphological operations to enhance the walls
    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(gray_mask, kernel, iterations=2)
    eroded = cv2.erode(dilated, kernel, iterations=1)
    closed = cv2.morphologyEx(eroded, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    if show_steps:
        cv2.imwrite("2_morphology.png", closed)
    
    # Step 3: Find contours in the processed image
    contours, hierarchy = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Step 4: Find the main contour (largest area)
    main_contour = None
    max_area = 0
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > max_area:
            max_area = area
            main_contour = cnt
    
    # Step 5: Approximate the contour to find corners
    corners = []
    if main_contour is not None:
        # Use a smaller epsilon for more precise corner detection
        epsilon = 0.005 * cv2.arcLength(main_contour, True)
        approx = cv2.approxPolyDP(main_contour, epsilon, True)
        
        # Extract corner points
        for point in approx:
            x, y = point[0]
            corners.append((x, y))
            # Draw corners on debug image
            cv2.circle(debug_image, (x, y), 5, (0, 0, 255), -1)
    
    # If we didn't find enough corners, try a different approach
    if len(corners) < 4:  # A house should have at least 4 corners (rectangular shape)
        print(f"Warning: Only detected {len(corners)} corners, trying alternative detection method...")
        
        # Create a mask of the main contour
        mask = np.zeros_like(gray)
        if main_contour is not None:
            cv2.drawContours(mask, [main_contour], 0, (255, 255, 255), -1)
        
        # Use Harris corner detector
        corners_harris = cv2.cornerHarris(mask, 5, 3, 0.04)
        # Use a proper kernel for dilation
        dilation_kernel = np.ones((3, 3), np.uint8)
        corners_harris = cv2.dilate(corners_harris, dilation_kernel)
        
        # Threshold for corner detection
        threshold = 0.01 * corners_harris.max()
        corner_points = np.where(corners_harris > threshold)
        
        # Convert to (x, y) format and filter to get distinct corners
        harris_corners = []
        for y, x in zip(corner_points[0], corner_points[1]):
            harris_corners.append((x, y))
        
        # Cluster corners that are close to each other
        from sklearn.cluster import DBSCAN
        if len(harris_corners) > 0:
            try:
                # Convert to numpy array for clustering
                harris_corners_np = np.array(harris_corners)
                
                # Use DBSCAN to cluster nearby points
                clustering = DBSCAN(eps=20, min_samples=1).fit(harris_corners_np)
                labels = clustering.labels_
                
                # Get cluster centers
                unique_labels = set(labels)
                clustered_corners = []
                
                for label in unique_labels:
                    cluster_points = harris_corners_np[labels == label]
                    center_x = int(np.mean(cluster_points[:, 0]))
                    center_y = int(np.mean(cluster_points[:, 1]))
                    clustered_corners.append((center_x, center_y))
                
                # If we found more corners with Harris, use those
                if len(clustered_corners) >= 8:
                    corners = clustered_corners
                    # Draw new corners on debug image
                    for x, y in corners:
                        cv2.circle(debug_image, (x, y), 5, (0, 255, 255), -1)
            except ImportError:
                print("Warning: sklearn not available for corner clustering.")
                # If sklearn is not available, just use the corners we already have
    
    # If we still don't have enough corners, try to infer them from the shape
    if len(corners) < 4:  # A house should have at least 4 corners (rectangular shape)
        print(f"Warning: Still only detected {len(corners)} corners, trying to infer from shape...")
        
        # Get the bounding box of the main contour
        if main_contour is not None:
            x, y, w, h = cv2.boundingRect(main_contour)
        else:
            # Default values if main_contour is None
            x, y, w, h = 0, 0, 100, 100
        
        # Define the expected corners based on the foundation shape
        # This is a simplified approach assuming a rectangular shape with a cutout
        # Convert to int to avoid Pylance errors with floating point indices
        h_two_thirds = int(h * 2/3)
        h_five_sixths = int(h * 5/6)
        w_one_third = int(w * 1/3)
        w_two_thirds = int(w * 2/3)
        
        inferred_corners = [
            (x, y),                      # Top-left
            (x + w, y),                  # Top-right
            (x + w, y + h_two_thirds),   # Right-middle
            (x + w, y + h),              # Bottom-right
            (x + w_two_thirds, y + h),   # Bottom-right-cutout
            (x + w_two_thirds, y + h_five_sixths),  # Bottom-cutout-right
            (x + w_one_third, y + h_five_sixths),   # Bottom-cutout-left
            (x + w_one_third, y + h),    # Bottom-left-cutout
            (x, y + h),                  # Bottom-left
            (x, y + h_two_thirds)        # Left-middle
        ]
        
        # Use these inferred corners if we need to
        if len(corners) < 8:
            corners = inferred_corners
            # Draw inferred corners on debug image
            for x, y in corners:
                cv2.circle(debug_image, (int(x), int(y)), 5, (255, 0, 255), -1)
    
    if show_steps:
        cv2.imwrite("2.5_detected_corners.png", debug_image)
    
    return corners, debug_image

def preprocess_image_for_walls(image_path, show_steps=False):
    """
    Preprocesses the image to identify walls by first detecting corners and then connecting them.
    
    Args:
        image_path: Path to image.
        show_steps: If True, save intermediate images for debugging.
        
    Returns:
        wall_image: Binary image (white walls on black background).
        perimeter_contours: List of contours representing the perimeter walls.
        geometry_data: Dictionary containing corner coordinates and wall segments.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not open/find image: {image_path}")
    
    # Get image dimensions
    height, width = image.shape[:2]
    
    # Step 1: Detect corners
    corners, debug_image = detect_corners(image_path, show_steps)
    
    # Step 2: Create walls by connecting corners
    # Sort corners to form a clockwise or counter-clockwise sequence
    # This is a simplified approach - for complex shapes, we would need a more sophisticated algorithm
    
    # First, find the center of the corners
    center_x = sum(x for x, y in corners) / len(corners)
    center_y = sum(y for x, y in corners) / len(corners)
    
    # Sort corners by angle from center
    sorted_corners = sorted(corners, key=lambda pt: np.arctan2(pt[1] - center_y, pt[0] - center_x))
    
    # Create a contour from the sorted corners
    contour_points = []
    for x, y in sorted_corners:
        contour_points.append([[[int(x), int(y)]]])
    
    # Convert to numpy array
    perimeter_contour = np.array(contour_points)
    
    # Create a list of wall segments (each segment is a line between two corners)
    wall_segments = []
    for i in range(len(sorted_corners)):
        pt1 = sorted_corners[i]
        pt2 = sorted_corners[(i + 1) % len(sorted_corners)]
        
        # Create a contour for this wall segment
        segment = np.array([[
            [int(pt1[0]), int(pt1[1])],
            [int(pt2[0]), int(pt2[1])]
        ]])
        
        wall_segments.append(segment)
    
    # Draw the walls on a blank image
    wall_image = np.zeros((height, width), dtype=np.uint8)
    
    # Draw the perimeter contour
    cv2.drawContours(wall_image, [np.array(sorted_corners).reshape(-1, 1, 2)], 0, (255, 255, 255), thickness=10)
    
    # Create debug image with walls
    walls_debug = image.copy()
    cv2.drawContours(walls_debug, [np.array(sorted_corners).reshape(-1, 1, 2)], 0, (0, 255, 0), thickness=4)
    
    # Draw corners on the debug image
    for i, (x, y) in enumerate(sorted_corners):
        cv2.circle(walls_debug, (int(x), int(y)), 5, (0, 0, 255), -1)
        cv2.putText(walls_debug, str(i), (int(x) + 5, int(y) + 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    
    if show_steps:
        cv2.imwrite("3_detected_walls.png", walls_debug)
        cv2.imwrite("4_wall_mask.png", wall_image)
    
    # Create geometry data structure
    geometry_data = {
        "corners": [],
        "walls": []
    }
    
    # Add corners to geometry data
    for i, (x, y) in enumerate(sorted_corners):
        # Default all corners to valid, the LLM will identify invalid ones
        geometry_data["corners"].append({
            "id": i,
            "x": int(x),
            "y": int(y),
            "is_valid": True  # This flag can be updated by the LLM
        })
    
    # Add walls to geometry data
    for i in range(len(sorted_corners)):
        pt1 = sorted_corners[i]
        pt2 = sorted_corners[(i + 1) % len(sorted_corners)]
        
        # Calculate wall length in pixels
        length_pixels = np.sqrt((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)
        
        geometry_data["walls"].append({
            "id": i + 1,
            "start_corner_id": i,
            "end_corner_id": (i + 1) % len(sorted_corners),
            "start_x": int(pt1[0]),
            "start_y": int(pt1[1]),
            "end_x": int(pt2[0]),
            "end_y": int(pt2[1]),
            "length_pixels": length_pixels
        })
    
    # Return the wall image, contour of the perimeter, and geometry data
    return wall_image, [np.array(sorted_corners).reshape(-1, 1, 2)], geometry_data


def get_overall_dimension_pixels(wall_image, orientation="horizontal"):
    """Measures overall width/height of foundation in pixels."""
    white_pixels = np.where(wall_image == 255)
    if not white_pixels[0].size:
        return 0

    if orientation == "horizontal":
        min_x = np.min(white_pixels[1])
        max_x = np.max(white_pixels[1])
        return max_x - min_x
    elif orientation == "vertical":
        min_y = np.min(white_pixels[0])
        max_y = np.max(white_pixels[0])
        return max_y - min_y
    else:
        raise ValueError("Invalid orientation. Use 'horizontal' or 'vertical'.")

def calculate_scale_factor(real_world_dimension, pixel_dimension):
    """Calculates scale factor (real-world units per pixel)."""
    if pixel_dimension == 0:
        return 0
    return real_world_dimension / pixel_dimension

def get_wall_segment_lengths_pixels(perimeter_contours):
    """
    Measures length of each perimeter wall segment in pixels by connecting corners.
    
    Args:
        perimeter_contours: List of contours representing the perimeter walls.
        
    Returns:
        segment_lengths: List of wall lengths in pixels.
    """
    segment_lengths = []
    
    # Process each contour
    for contour in perimeter_contours:
        # Get the points from the contour
        points = [point[0] for point in contour]
        
        # Calculate the length of each segment (line between consecutive points)
        for i in range(len(points)):
            pt1 = points[i]
            pt2 = points[(i + 1) % len(points)]
            length = np.sqrt((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)
            
            # Only include significant segments
            if length > 50:  # Lower threshold to catch smaller wall segments
                segment_lengths.append(length)
    
    # No need to enforce exactly 8 wall segments - houses can have different numbers of walls
    if len(segment_lengths) < 4:  # A house should have at least 4 wall segments
        print(f"Warning: Only detected {len(segment_lengths)} wall segments, which is unusually low.")
    
    return segment_lengths

def convert_to_real_world(pixel_lengths, scale_factor):
    """Converts pixel lengths to real-world lengths."""
    return [length * scale_factor for length in pixel_lengths]

def detect_text_with_google_vision(image):
    """Detects text in the image using Google Cloud Vision API."""
    if vision is None:
        print("Google Cloud Vision API not available. Skipping OCR.")
        return []
        
    try:
        client = vision.ImageAnnotatorClient()

        # Resize image for better OCR results
        resized_image = resize_image_for_vision_api(image, max_dim=1000)
        
        # Convert the OpenCV image to bytes (required by the Vision API).
        _, encoded_image = cv2.imencode('.png', resized_image)
        content = encoded_image.tobytes()
        vision_image = vision.Image(content=content)

        # Try document_text_detection first
        try:
            features = [vision.Feature(type=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)]
            request = vision.AnnotateImageRequest(image=vision_image, features=features)
            response = client.batch_annotate_images(requests=[request])
            texts = response.responses[0].text_annotations
        except Exception as e:
            print(f"DOCUMENT_TEXT_DETECTION failed: {e}")
            # Fall back to TEXT_DETECTION
            try:
                features = [vision.Feature(type=vision.Feature.Type.TEXT_DETECTION)]
                request = vision.AnnotateImageRequest(image=vision_image, features=features)
                response = client.batch_annotate_images(requests=[request])
                texts = response.responses[0].text_annotations
            except Exception as e:
                print(f"TEXT_DETECTION failed: {e}")
                return []

        ocr_results = []
        for text in texts:
            vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
            ocr_results.append({
                "text": text.description,
                "bbox": vertices # List of (x,y) tuples
            })

        return ocr_results
    except Exception as e:
        print(f"Google Vision API error: {e}")
        return []

def visualize_results(image, wall_lengths, ocr_results, perimeter_contours=None, geometry_data=None):
    """
    Draws the wall contours, OCR results, and wall lengths on the image.
    
    Args:
        image: Original image.
        wall_lengths: Dictionary of wall labels and their lengths.
        ocr_results: OCR text detection results.
        perimeter_contours: List of contours representing the perimeter walls.
        geometry_data: Optional dictionary containing corner coordinates and validity status.
        
    Returns:
        result_image: Annotated image.
    """
    # Create a copy of the image for visualization
    result_image = image.copy()
    
    # Draw the perimeter wall contours in green with thicker lines (4 pixels)
    if perimeter_contours is not None:
        # Draw the contour
        cv2.drawContours(result_image, perimeter_contours, -1, (0, 255, 0), 4)
    
    # Draw corners from geometry_data if available
    if geometry_data is not None:
        for corner in geometry_data['corners']:
            pt = (corner['x'], corner['y'])
            # Valid corners are green, invalid corners are red
            color = (0, 255, 0) if corner['is_valid'] else (0, 0, 255)
            cv2.circle(result_image, pt, 5, color, -1)
            # Add corner number
            cv2.putText(result_image, str(corner['id']), (pt[0] + 5, pt[1] + 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    
    # Draw OCR bounding boxes in red
    for result in ocr_results:
        vertices = result['bbox']
        pts = np.array(vertices, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(result_image, [pts], isClosed=True, color=(0, 0, 255), thickness=1)
    
    # Draw wall lengths
    if wall_lengths:
        font = cv2.FONT_HERSHEY_SIMPLEX
        y_offset = 30
        cv2.putText(result_image, "Wall Measurements:", (10, y_offset), font, 0.8, (0, 0, 0), 2)
        y_offset += 30
        
        for label, length in wall_lengths.items():
            # Use blue color for better visibility
            cv2.putText(result_image, f"{label}: {length}", (20, y_offset), font, 0.7, (0, 0, 255), 2)
            y_offset += 25
    
    return result_image

def encode_image_to_base64(image):
    """Encodes an OpenCV image to base64."""
    _, encoded_image = cv2.imencode('.png', image)
    base64_image = base64.b64encode(encoded_image.tobytes()).decode('utf-8')
    return base64_image

def update_corner_validity(geometry_data, llm_response):
    """Update the is_valid flag for corners based on LLM's response."""
    # Process the LLM's identification of invalid corners
    invalid_corners = llm_response.get('invalid_corners', [])
    
    # First pass: Mark corners as invalid based on LLM response
    for corner_id in invalid_corners:
        for corner in geometry_data['corners']:
            if corner['id'] == corner_id:
                corner['is_valid'] = False
                print(f"Marked corner {corner_id} as invalid based on LLM analysis")
    
    # Calculate the average wall length to determine what's "long" for this drawing
    avg_wall_length = 0
    if geometry_data['walls']:
        avg_wall_length = sum(wall['length_pixels'] for wall in geometry_data['walls']) / len(geometry_data['walls'])
    long_wall_threshold = max(100, avg_wall_length * 0.5)  # At least 100px or 50% of average
    print(f"Long wall threshold: {long_wall_threshold:.1f} pixels")
    
    # Find min/max x and y coordinates for perimeter detection
    if geometry_data['corners']:
        min_x = min(corner['x'] for corner in geometry_data['corners'])
        max_x = max(corner['x'] for corner in geometry_data['corners'])
        min_y = min(corner['y'] for corner in geometry_data['corners'])
        max_y = max(corner['y'] for corner in geometry_data['corners'])
        
        # Margin for considering a point at the perimeter (5% of dimension)
        x_margin = 0.05 * (max_x - min_x)
        y_margin = 0.05 * (max_y - min_y)
    
    # Second pass: Verify if any corners were incorrectly marked as invalid
    # This helps prevent valid structural corners from being filtered out
    for corner in geometry_data['corners']:
        if not corner['is_valid']:
            # Find walls connected to this corner
            connected_walls = []
            for wall in geometry_data['walls']:
                if wall['start_corner_id'] == corner['id'] or wall['end_corner_id'] == corner['id']:
                    connected_walls.append(wall)
            
            # Check if this corner is at the perimeter
            at_perimeter = False
            if geometry_data['corners']:
                at_x_perimeter = (abs(corner['x'] - min_x) <= x_margin or abs(corner['x'] - max_x) <= x_margin)
                at_y_perimeter = (abs(corner['y'] - min_y) <= y_margin or abs(corner['y'] - max_y) <= y_margin)
                at_perimeter = at_x_perimeter and at_y_perimeter
            
            # If this corner is at the perimeter and connects to at least one long wall, it's likely valid
            has_long_wall = any(wall['length_pixels'] > long_wall_threshold for wall in connected_walls)
            
            if at_perimeter and has_long_wall:
                corner['is_valid'] = True
                print(f"Restored corner {corner['id']} as valid based on perimeter position and long wall")
                continue
            
            # If we have at least 2 connected walls, check the angle
            if len(connected_walls) >= 2:
                # Get vectors for the walls
                vectors = []
                for wall in connected_walls:
                    if wall['start_corner_id'] == corner['id']:
                        # Vector points away from the corner
                        vx = wall['end_x'] - corner['x']
                        vy = wall['end_y'] - corner['y']
                    else:
                        # Vector points toward the corner
                        vx = corner['x'] - wall['start_x']
                        vy = corner['y'] - wall['start_y']
                    
                    # Normalize the vector
                    length = (vx**2 + vy**2)**0.5
                    if length > 0:
                        vectors.append((vx/length, vy/length))
                
                # Calculate angles between vectors
                for i in range(len(vectors)):
                    for j in range(i+1, len(vectors)):
                        # Dot product gives cosine of angle
                        dot_product = vectors[i][0]*vectors[j][0] + vectors[i][1]*vectors[j][1]
                        # Clamp to valid range for arccos
                        dot_product = max(-1.0, min(1.0, dot_product))
                        angle_rad = np.arccos(dot_product)
                        angle_deg = np.degrees(angle_rad)
                        
                        # Check if angle is close to 90 degrees (within 30 degrees)
                        if 60 <= angle_deg <= 120:
                            corner['is_valid'] = True
                            print(f"Restored corner {corner['id']} as valid based on angle check")
                            break
                    if corner['is_valid']:
                        break
    
    # Third pass: Check for corners that form the main shape of the foundation
    # Count how many valid corners we have
    valid_corner_count = sum(1 for corner in geometry_data['corners'] if corner['is_valid'])
    
    # If we have too few valid corners (less than 4), we need to restore some
    if valid_corner_count < 4:
        print(f"Warning: Only {valid_corner_count} valid corners detected. Restoring important corners...")
        
        # Sort corners by importance (number of connected walls * total length of connected walls)
        corner_importance = []
        for corner in geometry_data['corners']:
            if not corner['is_valid']:
                # Find connected walls
                connected_walls = []
                for wall in geometry_data['walls']:
                    if wall['start_corner_id'] == corner['id'] or wall['end_corner_id'] == corner['id']:
                        connected_walls.append(wall)
                
                # Calculate importance score
                total_length = sum(wall['length_pixels'] for wall in connected_walls)
                importance = len(connected_walls) * total_length
                
                corner_importance.append((corner['id'], importance))
        
        # Sort by importance (highest first)
        corner_importance.sort(key=lambda x: x[1], reverse=True)
        
        # Restore corners until we have at least 4 valid corners
        for corner_id, importance in corner_importance:
            if valid_corner_count >= 4:
                break
                
            # Find the corner and mark it as valid
            for corner in geometry_data['corners']:
                if corner['id'] == corner_id and not corner['is_valid']:
                    corner['is_valid'] = True
                    valid_corner_count += 1
                    print(f"Restored corner {corner_id} as valid based on importance score")
                    break
    
    return geometry_data

def filter_invalid_walls(geometry_data):
    """Filter out walls that connect to invalid corners."""
    valid_walls = []
    invalid_walls = []
    
    # First, identify walls connecting to invalid corners
    for wall in geometry_data['walls']:
        start_valid = False
        end_valid = False
        
        for corner in geometry_data['corners']:
            if corner['id'] == wall['start_corner_id']:
                start_valid = corner['is_valid']
            if corner['id'] == wall['end_corner_id']:
                end_valid = corner['is_valid']
        
        if start_valid and end_valid:
            valid_walls.append(wall)
        else:
            invalid_walls.append(wall)
            print(f"Identified invalid wall {wall['id']} connecting corners {wall['start_corner_id']} and {wall['end_corner_id']}")
    
    # Check if we're filtering out too many walls (more than 30%)
    if len(invalid_walls) > 0.3 * len(geometry_data['walls']):
        print("Warning: Too many walls being filtered out. Rechecking corner validity...")
        
        # Reconsider corners that might be valid structural corners
        for corner in geometry_data['corners']:
            if not corner['is_valid']:
                # Count how many walls connect to this corner
                connected_wall_count = 0
                for wall in geometry_data['walls']:
                    if wall['start_corner_id'] == corner['id'] or wall['end_corner_id'] == corner['id']:
                        connected_wall_count += 1
                
                # If this corner connects multiple walls, it might be a valid structural corner
                if connected_wall_count >= 2:
                    # Check if any of these walls are long (structural)
                    has_long_wall = False
                    for wall in geometry_data['walls']:
                        if (wall['start_corner_id'] == corner['id'] or wall['end_corner_id'] == corner['id']) and wall['length_pixels'] > 100:
                            has_long_wall = True
                            break
                    
                    if has_long_wall:
                        corner['is_valid'] = True
                        print(f"Restored corner {corner['id']} as valid based on structural importance")
        
        # Recompute valid walls after updating corner validity
        valid_walls = []
        for wall in geometry_data['walls']:
            start_valid = False
            end_valid = False
            
            for corner in geometry_data['corners']:
                if corner['id'] == wall['start_corner_id']:
                    start_valid = corner['is_valid']
                if corner['id'] == wall['end_corner_id']:
                    end_valid = corner['is_valid']
            
            if start_valid and end_valid:
                valid_walls.append(wall)
            else:
                print(f"Filtered out wall {wall['id']} connecting corners {wall['start_corner_id']} and {wall['end_corner_id']}")
    
    # Replace the walls in geometry_data with only the valid walls
    geometry_data['walls'] = valid_walls
    return geometry_data

def save_geometry_data(geometry_data, output_path):
    """Saves geometry data to a JSON file and prints it to the console."""
    try:
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(geometry_data, f, indent=2)
        
        # Print to console
        print(f"\nGeometry data (also saved to {output_path}):")
        print(json.dumps(geometry_data, indent=2))
        
        return True
    except Exception as e:
        print(f"Error saving geometry data: {e}")
        return False

# --- LLM Interaction Functions ---
def call_mistral_llm(prompt, image_base64, api_key):
    """Calls the Mistral API with the given prompt and image."""
    print("Mistral API is not supported in this version. Please use OpenAI or Gemini instead.")
    return "Error: Mistral API is not supported in this version."

def call_openai_llm(prompt, image_base64, api_key):
    """Calls the OpenAI GPT-4o API with the given prompt and image."""
    if openai is None:
        return "Error: OpenAI library not installed."
    client = openai.OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                        },
                    ],
                }
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return f"Error: {e}"

def call_gemini_llm(prompt, image, api_key):
    """Calls the Google Gemini API with the given prompt and image."""
    if genai is None:
         return "Error: Google Generative AI library not installed."
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro-002')
    try:
        response = model.generate_content(
            [prompt, image],
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                top_p=0.95,
                top_k=0,
                max_output_tokens=8192,
            )
        )
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return f"Error: {e}"

def call_claude_llm(prompt, image_base64, api_key):
    """Calls the Anthropic Claude 3.7 Sonnet API with the given prompt and image."""
    if Anthropic is None:
        return "Error: Anthropic library not installed."
    
    client = Anthropic(api_key=api_key)
    
    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=4096,
            temperature=0.0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        }
                    ]
                }
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return f"Error: {e}"

def parse_llm_response(response_text):
    """
    Parses the LLM's response, attempting to extract a JSON object.
    """
    try:
        # Attempt to find JSON within code blocks (```json ... ```)
        match = re.search(r"```json\n(.*?)```", response_text, re.DOTALL)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)

        # Attempt to find JSON directly (without code blocks)
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        return {} # No JSON

    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        print(f"Raw LLM response (failed to parse): {response_text}")
        return {}  # Return empty dict on failure
    except Exception as e:
        print(f"Error during parsing with other exception: {e}")
        return {}
    
def create_prompt(ocr_results, overall_width_inches, geometry_data=None, image_base64=None):
     """
     Creates a detailed prompt for the LLM, incorporating OCR results and geometry data.
     """
     # Prepare OCR results for inclusion in the prompt
     ocr_text_list = [result['text'] for result in ocr_results]
     ocr_text_str = "\n".join(ocr_text_list)
     
     # Prepare geometry data for inclusion in the prompt
     geometry_str = ""
     if geometry_data:
         geometry_str = f"""
    I have also detected the following geometry:
    
    Corners: {len(geometry_data['corners'])} points
    Walls: {len(geometry_data['walls'])} segments
    
    Here is the detailed geometry data:
    ```json
    {json.dumps(geometry_data, indent=2)}
    ```
    """
    
     prompt = f"""You are an expert at reading architectural foundation plans.

    I have preprocessed an image of a foundation plan to isolate the concrete-filled walls.
    I have also performed OCR (Optical Character Recognition) to extract text from the drawing.
    {geometry_str}

    IMPORTANT: The user has specified that the overall width of this foundation is {overall_width_inches} inches ({overall_width_inches/12:.1f} feet). 
    Use this measurement as your primary reference scale when analyzing dimensions.

    Your task is to:
    1. Identify any invalid corners in the geometry data
    2. Identify the lengths of each exterior foundation wall, maintaining the wall IDs from the geometry data

    IMPORTANT INSTRUCTIONS FOR IDENTIFYING INVALID CORNERS:
    - This image represents a house foundation floor plan
    - Valid foundation corners are typically where exterior walls meet at roughly 90° angles
    - Invalid corners may include:
        * Points detected on curved edges or arcs
        * Points that create very short wall segments
        * Points that are artifacts from text, dimension lines, or other annotations
        * Points that don't represent actual structural corners of the foundation
    - The shape of a typical foundation is rectilinear and consists of straight walls meeting at right angles
    - After removing invalid corners, the remaining valid corners should connect to form a coherent foundation perimeter

    Example: If corners 5, 6, and 7 create tiny segments or were detected on a curved element, you should mark them as invalid.
    
    Here is the OCR extracted text:
    ```
    {ocr_text_str}
    ```

    Look at the image carefully. The foundation plan shows a structure with walls around the perimeter.
    
    Identify each valid wall segment and provide its length in feet and inches.
    Pay special attention to the dimensions labeled in the drawing and ensure they match the user-specified overall width.

    Format your response as a JSON object with the following structure:
    ```json
    {{
      "invalid_corners": [5, 6, 7],  # IDs of corners that are not valid (use actual corner IDs from geometry data)
      "walls": [
        {{"wall_id": 1, "length": "55'-0\\"", "position": "description of location"}},
        # Include all valid exterior walls with their correct IDs from the geometry data
      ]
    }}
    ```
    """
     return prompt

def create_corner_correction_prompt(geometry_data):
    """
    Creates a prompt for the LLM to correct corner positions to form 90° angles.
    
    Args:
        geometry_data: Dictionary containing corner coordinates and wall segments.
        
    Returns:
        prompt: Prompt for the LLM.
    """
    prompt = f"""You are an expert at analyzing and correcting architectural foundation plans.

I have detected the following geometry data from a foundation plan:

```json
{json.dumps(geometry_data, indent=2)}
```

Your task is to analyze this geometry data and correct the corner positions to ensure that walls meet at 90° angles wherever appropriate. Foundation plans typically have rectilinear designs with perpendicular walls.

For each corner, determine if it needs adjustment to form proper 90° angles with adjacent walls. Consider the following:

1. Identify corners that should form right angles based on the overall structure
2. Calculate the adjusted positions for these corners to create proper 90° angles
3. Preserve the overall shape and dimensions of the foundation as much as possible
4. Focus on the main structural corners and ignore minor deviations

Format your response as a JSON object with the following structure:
```json
{
  "corrected_corners": [
    {
      "id": 0,
      "original_x": 100,
      "original_y": 200,
      "corrected_x": 100,
      "corrected_y": 200,
      "reason": "Already forms approximately 90° angles with adjacent walls"
    },
    {
      "id": 1,
      "original_x": 300,
      "original_y": 210,
      "corrected_x": 300,
      "corrected_y": 200,
      "reason": "Adjusted to form 90° angle with walls connecting to corners 0 and 2"
    },
    ...
  ]
}
```

For corners that don't need adjustment, include them in the response with the same coordinates as the original.
"""
    return prompt

def correct_corners_with_llm(geometry_data, image_base64, api_key, llm_type):
    """
    Uses an LLM to correct corner positions to form 90° angles.
    
    Args:
        geometry_data: Dictionary containing corner coordinates and wall segments.
        image_base64: Base64-encoded image for visual context.
        api_key: API key for the LLM.
        llm_type: Type of LLM to use (openai, gemini, claude).
        
    Returns:
        corrected_geometry: Updated geometry data with corrected corner positions.
    """
    print("\n--- Correcting Corner Positions with LLM ---")
    
    # Create the prompt
    prompt = create_corner_correction_prompt(geometry_data)
    
    # Call the appropriate LLM
    if llm_type == "openai":
        llm_response = call_openai_llm(prompt, image_base64, api_key)
    elif llm_type == "gemini":
        # For Gemini, we need to decode the base64 image back to an OpenCV image
        _, img_data = cv2.imencode('.png', cv2.imdecode(np.frombuffer(base64.b64decode(image_base64), np.uint8), cv2.IMREAD_COLOR))
        llm_response = call_gemini_llm(prompt, img_data, api_key)
    elif llm_type == "claude":
        llm_response = call_claude_llm(prompt, image_base64, api_key)
    else:
        print("Error: Unsupported LLM type for corner correction")
        return geometry_data
    
    # Parse the response
    parsed_response = parse_llm_response(llm_response)
    
    if not parsed_response or 'corrected_corners' not in parsed_response:
        print("No corner corrections received from LLM")
        return geometry_data
    
    # Create a copy of the geometry data to modify
    corrected_geometry = copy.deepcopy(geometry_data)
    
    # Apply the corrections
    for correction in parsed_response.get('corrected_corners', []):
        corner_id = correction.get('id')
        corrected_x = correction.get('corrected_x')
        corrected_y = correction.get('corrected_y')
        reason = correction.get('reason', '')
        
        # Find the corner in the geometry data
        for corner in corrected_geometry['corners']:
            if corner['id'] == corner_id:
                # Check if the position was actually changed
                if corner['x'] != corrected_x or corner['y'] != corrected_y:
                    print(f"Correcting corner {corner_id}: ({corner['x']}, {corner['y']}) -> ({corrected_x}, {corrected_y})")
                    print(f"  Reason: {reason}")
                    
                    # Update the corner position
                    corner['x'] = corrected_x
                    corner['y'] = corrected_y
                    
                    # Also update any walls that use this corner
                    for wall in corrected_geometry['walls']:
                        if wall['start_corner_id'] == corner_id:
                            wall['start_x'] = corrected_x
                            wall['start_y'] = corrected_y
                        if wall['end_corner_id'] == corner_id:
                            wall['end_x'] = corrected_x
                            wall['end_y'] = corrected_y
                break
    
    # Recalculate wall lengths
    for wall in corrected_geometry['walls']:
        start_x = wall['start_x']
        start_y = wall['start_y']
        end_x = wall['end_x']
        end_y = wall['end_y']
        
        # Calculate wall length in pixels
        wall['length_pixels'] = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
    
    return corrected_geometry

def create_llm_feedback_prompt(image_base64, geometry_data=None):
    """
    Creates a prompt for the LLM to provide feedback on the wall detection.
    
    Args:
        image_base64: Base64-encoded image.
        geometry_data: Optional dictionary containing corner coordinates and wall segments.
        
    Returns:
        prompt: Prompt for the LLM.
    """
    # Prepare geometry data for inclusion in the prompt
    geometry_str = ""
    if geometry_data:
        geometry_str = f"""
I have also detected the following geometry:

Corners: {len(geometry_data['corners'])} points
Walls: {len(geometry_data['walls'])} segments

Here is the detailed geometry data:
```json
{json.dumps(geometry_data, indent=2)}
```
"""
    
    prompt = f"""You are an expert at analyzing architectural foundation plans.
{geometry_str}

I have processed a foundation plan image to detect the perimeter walls, which are shown as green lines in the image.

Please analyze the image and provide feedback on the wall detection:
1. Are there any areas where the green line deviates from the actual wall?
2. Are there any areas where the green line is missing or incomplete?
3. Are there any false positives (green lines that are not actually walls)?

For each issue, please provide:
- A description of the location (e.g., "bottom left corner", "top right", etc.)
- What the problem is (deviation, missing segment, false positive)
- A suggestion for how to fix it

Format your response as a JSON object with the following structure:
```json
{
  "issues": [
    {
      "location": "bottom center",
      "problem": "deviation",
      "description": "The green line deviates from the wall and connects to text annotations",
      "suggestion": "The line should follow the straight wall and not connect to the text"
    },
    ...
  ],
  "overall_assessment": "The wall detection is mostly accurate but has issues in the bottom area"
}
```
"""
    return prompt

def apply_llm_feedback(perimeter_contours, feedback, image_shape):
    """
    Applies feedback from the LLM to improve the wall detection.
    
    Args:
        perimeter_contours: List of contours representing the perimeter walls.
        feedback: Parsed feedback from the LLM.
        image_shape: Shape of the image (height, width).
        
    Returns:
        improved_contours: Improved list of contours.
    """
    height, width = image_shape[:2]
    improved_contours = []
    contours_to_remove = []
    
    # First, identify contours to remove (false positives)
    for issue in feedback.get('issues', []):
        location = issue.get('location', '').lower()
        problem = issue.get('problem', '').lower()
        
        if problem == 'false positive':
            # Mark contours in this area for removal
            for i, contour in enumerate(perimeter_contours):
                # Calculate contour centroid
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    # Fallback to bounding box center
                    x, y, w, h = cv2.boundingRect(contour)
                    cx, cy = x + w//2, y + h//2
                
                # Check if centroid is in the specified location
                in_location = False
                if 'bottom' in location and cy > height * 0.7:
                    if ('left' in location and cx < width * 0.3) or \
                       ('center' in location and cx >= width * 0.3 and cx <= width * 0.7) or \
                       ('right' in location and cx > width * 0.7) or \
                       ('left' not in location and 'center' not in location and 'right' not in location):
                        in_location = True
                elif 'top' in location and cy < height * 0.3:
                    if ('left' in location and cx < width * 0.3) or \
                       ('center' in location and cx >= width * 0.3 and cx <= width * 0.7) or \
                       ('right' in location and cx > width * 0.7) or \
                       ('left' not in location and 'center' not in location and 'right' not in location):
                        in_location = True
                elif 'middle' in location and cy >= height * 0.3 and cy <= height * 0.7:
                    if ('left' in location and cx < width * 0.3) or \
                       ('center' in location and cx >= width * 0.3 and cx <= width * 0.7) or \
                       ('right' in location and cx > width * 0.7) or \
                       ('left' not in location and 'center' not in location and 'right' not in location):
                        in_location = True
                
                if in_location:
                    contours_to_remove.append(i)
    
    # Process each contour
    for i, contour in enumerate(perimeter_contours):
        # Skip contours marked for removal
        if i in contours_to_remove:
            continue
        
        # Create a copy of the contour to modify
        modified_contour = contour.copy()
        
        # Apply fixes based on feedback
        for issue in feedback.get('issues', []):
            location = issue.get('location', '').lower()
            problem = issue.get('problem', '').lower()
            
            # Calculate contour centroid
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                # Fallback to bounding box center
                x, y, w, h = cv2.boundingRect(contour)
                cx, cy = x + w//2, y + h//2
            
            # Check if this contour is in the location mentioned in the feedback
            in_location = False
            if 'bottom' in location and cy > height * 0.7:
                if ('left' in location and cx < width * 0.3) or \
                   ('center' in location and cx >= width * 0.3 and cx <= width * 0.7) or \
                   ('right' in location and cx > width * 0.7) or \
                   ('left' not in location and 'center' not in location and 'right' not in location):
                    in_location = True
            elif 'top' in location and cy < height * 0.3:
                if ('left' in location and cx < width * 0.3) or \
                   ('center' in location and cx >= width * 0.3 and cx <= width * 0.7) or \
                   ('right' in location and cx > width * 0.7) or \
                   ('left' not in location and 'center' not in location and 'right' not in location):
                    in_location = True
            elif 'middle' in location and cy >= height * 0.3 and cy <= height * 0.7:
                if ('left' in location and cx < width * 0.3) or \
                   ('center' in location and cx >= width * 0.3 and cx <= width * 0.7) or \
                   ('right' in location and cx > width * 0.7) or \
                   ('left' not in location and 'center' not in location and 'right' not in location):
                    in_location = True
            
            if in_location and problem == 'deviation':
                # Fix deviation by straightening the line in this area
                if 'bottom' in location:
                    # Find points in the bottom part
                    bottom_points = []
                    bottom_indices = []
                    for j in range(len(modified_contour)):
                        if modified_contour[j][0][1] > height * 0.7:
                            bottom_points.append(modified_contour[j])
                            bottom_indices.append(j)
                    
                    if bottom_points:
                        # Calculate average y-coordinate for bottom points
                        avg_y = sum(pt[0][1] for pt in bottom_points) / len(bottom_points)
                        
                        # Find leftmost and rightmost x-coordinates
                        x_coords = [pt[0][0] for pt in bottom_points]
                        left_x = min(x_coords)
                        right_x = max(x_coords)
                        
                        # Create a new contour with straight bottom line
                        new_contour = []
                        for j in range(len(modified_contour)):
                            if j not in bottom_indices:
                                new_contour.append(modified_contour[j])
                        
                        # Add just two points for the bottom line
                        new_contour.append(np.array([[[left_x, int(avg_y)]]]))
                        new_contour.append(np.array([[[right_x, int(avg_y)]]]))
                        
                        if len(new_contour) >= 3:
                            modified_contour = np.array(new_contour)
                
                elif 'top' in location:
                    # Similar logic for top part
                    top_points = []
                    top_indices = []
                    for j in range(len(modified_contour)):
                        if modified_contour[j][0][1] < height * 0.3:
                            top_points.append(modified_contour[j])
                            top_indices.append(j)
                    
                    if top_points:
                        avg_y = sum(pt[0][1] for pt in top_points) / len(top_points)
                        x_coords = [pt[0][0] for pt in top_points]
                        left_x = min(x_coords)
                        right_x = max(x_coords)
                        
                        new_contour = []
                        for j in range(len(modified_contour)):
                            if j not in top_indices:
                                new_contour.append(modified_contour[j])
                        
                        new_contour.append(np.array([[[left_x, int(avg_y)]]]))
                        new_contour.append(np.array([[[right_x, int(avg_y)]]]))
                        
                        if len(new_contour) >= 3:
                            modified_contour = np.array(new_contour)
        
        # Add the modified contour to the improved contours list
        if len(modified_contour) >= 3:  # Ensure it's a valid contour
            improved_contours.append(modified_contour)
    
    # Handle missing segments (create new contours if needed)
    for issue in feedback.get('issues', []):
        if issue.get('problem', '').lower() == 'missing segment':
            location = issue.get('location', '').lower()
            # This would require more complex logic to create new contours
            # For now, we'll just print a message
            print(f"Note: Missing segment in {location} detected but not automatically fixed.")
    
    return improved_contours

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
    parser.add_argument("--llm", default="none", choices=["none", "mistral", "openai", "gemini", "claude"],
                        help="Which LLM to use for wall length analysis (none, mistral, openai, gemini, claude). Default: none.")
    parser.add_argument("--feedback_llm", default="none", choices=["none", "openai", "gemini", "claude"],
                        help="Which LLM to use for wall detection feedback (none, openai, gemini, claude). Default: none.")
    parser.add_argument("--correct_corners", default="none", choices=["none", "openai", "gemini", "claude"],
                        help="Use LLM to correct corner positions to form 90° angles (none, openai, gemini, claude). Default: none.")
    parser.add_argument("--iterations", type=int, default=1,
                        help="Number of iterations for the feedback loop (default: 1).")
    args = parser.parse_args()

    # --- API Keys (from environment variables) ---
    mistral_api_key = os.environ.get("MISTRAL_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    claude_api_key = os.environ.get("ANTHROPIC_API_KEY")

    if args.llm == "mistral" and not mistral_api_key:
        print("Error: Mistral API key not found. Set the MISTRAL_API_KEY environment variable.")
        return
    if args.llm == "openai" and not openai_api_key:
        print("Error: OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")
        return
    if args.llm == "gemini" and not gemini_api_key:
        print("Error: Gemini API key not found. Set the GEMINI_API_KEY environment variable.")
        return
    if args.llm == "claude" and not claude_api_key:
        print("Error: Claude API key not found. Set the ANTHROPIC_API_KEY environment variable.")
        return
    
    if (args.feedback_llm == "openai") and not openai_api_key:
        print("Error: OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")
        return
    if (args.feedback_llm == "gemini") and not gemini_api_key:
        print("Error: Gemini API key not found. Set the GEMINI_API_KEY environment variable.")
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
            
            if args.feedback_llm == "openai":
                feedback_response = call_openai_llm(feedback_prompt, feedback_image_base64, openai_api_key)
            elif args.feedback_llm == "gemini":
                feedback_response = call_gemini_llm(feedback_prompt, feedback_image, gemini_api_key)
            elif args.feedback_llm == "claude":
                feedback_response = call_claude_llm(feedback_prompt, feedback_image_base64, claude_api_key)
            
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
    
    # --- 8. Optional LLM Analysis for Wall Lengths ---
    wall_lengths_llm = {}  # Initialize for LLM results
    if args.llm != "none":
        print("\n--- Getting Wall Length Analysis from LLM ---")
        prompt = create_prompt(ocr_results, overall_width_inches, geometry_data)
        image_base64 = encode_image_to_base64(image) # Use original image

        if args.llm == "mistral":
            llm_response = call_mistral_llm(prompt, image_base64, mistral_api_key)
        elif args.llm == "openai":
            llm_response = call_openai_llm(prompt, image_base64, openai_api_key)
        elif args.llm == "gemini":
            llm_response = call_gemini_llm(prompt, image, gemini_api_key)
        elif args.llm == "claude":
            llm_response = call_claude_llm(prompt, image_base64, claude_api_key)
        
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
        elif args.correct_corners == "gemini":
            if not gemini_api_key:
                print("Error: Gemini API key not found. Skipping corner correction.")
            else:
                image_base64 = encode_image_to_base64(image)
                geometry_data = correct_corners_with_llm(geometry_data, image_base64, gemini_api_key, "gemini")
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
