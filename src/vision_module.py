#!/usr/bin/env python3
# pyright: reportIndexIssue=false
# pyright: reportMissingModuleSource=false
import os
import base64
import json
import cv2
import numpy as np
from typing import List, Dict, Tuple, Any, Sequence, Optional, Union
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    from google.cloud import vision
except ImportError:
    print("Warning: Google Cloud Vision package not installed. Vision features will not work.")
    vision = None

try:
    from sklearn.cluster import DBSCAN  # type: ignore
except ImportError:
    print("Warning: sklearn not installed. Advanced corner clustering will not work.")
    DBSCAN = None

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
        if len(harris_corners) > 0 and DBSCAN is not None:
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
        # Use intermediate variables to avoid type errors
        h_two_thirds_float = float(h) * 2/3
        h_five_sixths_float = float(h) * 5/6
        w_one_third_float = float(w) * 1/3
        w_two_thirds_float = float(w) * 2/3
        
        h_two_thirds = int(h_two_thirds_float)
        h_five_sixths = int(h_five_sixths_float)
        w_one_third = int(w_one_third_float)
        w_two_thirds = int(w_two_thirds_float)
        
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
        # Check if we have JSON credentials directly in environment variable
        google_credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if google_credentials_json:
            import json
            from google.oauth2 import service_account
            import io
            
            # Parse the JSON credentials
            credentials_info = json.loads(google_credentials_json)
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            client = vision.ImageAnnotatorClient(credentials=credentials)
        else:
            # Use the default credentials from GOOGLE_APPLICATION_CREDENTIALS
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

def detect_corners_for_perimeter(image_path, show_steps=False):
    """
    Enhanced corner detection optimized for foundation perimeter extraction.
    
    Args:
        image_path: Path to image.
        show_steps: If True, save intermediate images for debugging.
        
    Returns:
        corners: List of potential corner points (x, y) coordinates.
        clean_image: Image with only corner points visualized.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not open/find image: {image_path}")
    
    # Create a clean copy for visualization
    clean_image = image.copy()
    
    # Use multiple corner detection methods for comprehensive results
    corners = []
    
    # Method 1: Our existing contour-based corner detection
    detected_corners, _ = detect_corners(image_path, show_steps=False)
    corners.extend(detected_corners)
    
    # Method 2: Harris corner detector for additional points
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    harris_corners = cv2.cornerHarris(gray, blockSize=5, ksize=3, k=0.04)
    # Use a proper kernel for dilation
    dilation_kernel = np.ones((3, 3), np.uint8)
    harris_corners = cv2.dilate(harris_corners, dilation_kernel)
    threshold = 0.01 * harris_corners.max()
    
    # Find coordinates where harris_corners exceeds threshold
    corner_points = np.where(harris_corners > threshold)
    for y, x in zip(corner_points[0], corner_points[1]):
        corners.append((x, y))
    
    # Remove duplicates by clustering nearby points
    if len(corners) > 0 and DBSCAN is not None:
        try:
            corners_np = np.array(corners)
            # Adjust epsilon based on image size
            epsilon = min(image.shape[0], image.shape[1]) * 0.015  # 1.5% of image dimension
            clustering = DBSCAN(eps=epsilon, min_samples=1).fit(corners_np)
            labels = clustering.labels_
            
            unique_labels = set(labels)
            clustered_corners = []
            
            for label in unique_labels:
                cluster_points = corners_np[labels == label]
                center_x = int(np.mean(cluster_points[:, 0]))
                center_y = int(np.mean(cluster_points[:, 1]))
                clustered_corners.append((center_x, center_y))
            
            corners = clustered_corners
        except Exception as e:
            print(f"Error during corner clustering: {e}")
    
    # Create a visualization with only the corner points (no text or OCR)
    for i, (x, y) in enumerate(corners):
        # Draw a clearly visible marker for each potential corner
        cv2.circle(clean_image, (int(x), int(y)), 8, (0, 0, 255), -1)  # RED dot
        cv2.circle(clean_image, (int(x), int(y)), 8, (0, 0, 0), 2)     # Black outline
        
        # Add ID number near the point with better visibility
        text_x = int(x) + 10
        text_y = int(y) + 5
        # Draw white background for better contrast
        cv2.putText(clean_image, str(i), (text_x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 5)  # White background/outline
        # Draw text in black
        cv2.putText(clean_image, str(i), (text_x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)        # Black text
    
    if show_steps:
        cv2.imwrite("corners_for_perimeter.png", clean_image)
    
    return corners, clean_image

def calculate_perimeter_scale(overall_width_inches, corner_points):
    """
    Calculate scale factor based on overall width and the identified corner points.
    
    Args:
        overall_width_inches: Width of the foundation in inches as provided by user.
        corner_points: List of (x,y) coordinates of potential corner points.
        
    Returns:
        scale_factor: Inches per pixel.
    """
    # Find the bounding box of all points
    x_coords = [x for x, y in corner_points]
    min_x = min(x_coords)
    max_x = max(x_coords)
    
    # Calculate the width in pixels
    width_pixels = max_x - min_x
    
    # Calculate scale factor (inches per pixel)
    if width_pixels == 0:
        return 1.0  # Fallback
    
    scale_factor = overall_width_inches / width_pixels
    print(f"Calculated scale: {scale_factor:.4f} inches per pixel")
    print(f"Width in pixels: {width_pixels}, Width in inches: {overall_width_inches}")
    
    return scale_factor

def prepare_geometry_data_for_llm(corners):
    """
    Prepare geometry data for LLM analysis, focusing only on corner points.
    
    Args:
        corners: List of (x,y) coordinates of potential corner points.
        
    Returns:
        geometry_data: Dictionary with corner coordinates for LLM analysis.
    """
    geometry_data = {
        "corners": []
    }
    
    # Add corners to geometry data with IDs
    for i, (x, y) in enumerate(corners):
        geometry_data["corners"].append({
            "id": i,
            "x": int(x),
            "y": int(y)
        })
    
    return geometry_data

def calculate_wall_lengths(perimeter_model, scale_factor):
    """
    Calculate wall lengths based on pixel distances and scale factor.
    
    Args:
        perimeter_model: Foundation model with corners and walls.
        scale_factor: Scale factor in inches per pixel.
        
    Returns:
        wall_lengths: Dictionary of wall lengths in feet and inches.
    """
    wall_lengths = {}
    
    for wall in perimeter_model['walls']:
        # Calculate length in inches
        length_inches = wall['length_pixels'] * scale_factor
        
        # Convert to feet and inches
        feet = int(length_inches // 12)
        inches = int(round(length_inches % 12))
        
        # Handle the case where inches is 12 (roll over to the next foot)
        if inches == 12:
            feet += 1
            inches = 0
        
        # Format as string
        wall_lengths[wall['id']] = f"{feet}'-{inches}\""
        
        # Add to the wall object
        wall['length'] = wall_lengths[wall['id']]
    
    return wall_lengths

def create_perimeter_model(geometry_data, perimeter_corner_ids):
    """
    Create a clean perimeter model from identified corner IDs.
    
    Args:
        geometry_data: Original geometry data with corner coordinates.
        perimeter_corner_ids: List of corner IDs that form the perimeter, in order.
        
    Returns:
        perimeter_model: Foundation perimeter model with corners and walls.
    """
    if not perimeter_corner_ids:
        print("Error: No perimeter corners identified")
        return None
    
    # Create clean perimeter model
    perimeter_model = {
        "corners": [],
        "walls": []
    }
    
    # Add identified corners to perimeter model with new sequential IDs
    id_mapping = {}  # Map from original IDs to new sequential IDs
    
    for new_id, original_id in enumerate(perimeter_corner_ids):
        for corner in geometry_data['corners']:
            if corner['id'] == original_id:
                # Add this corner to perimeter model with new ID
                perimeter_model['corners'].append({
                    "id": new_id,
                    "x": corner['x'],
                    "y": corner['y'],
                    "original_id": original_id
                })
                id_mapping[original_id] = new_id
                break
    
    # Create walls connecting corners in sequence
    num_corners = len(perimeter_model['corners'])
    for i in range(num_corners):
        start_corner = perimeter_model['corners'][i]
        end_corner = perimeter_model['corners'][(i + 1) % num_corners]
        
        # Calculate wall length in pixels
        start_x, start_y = start_corner['x'], start_corner['y']
        end_x, end_y = end_corner['x'], end_corner['y']
        length_pixels = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        
        perimeter_model['walls'].append({
            "id": i + 1,
            "start_corner_id": start_corner['id'],
            "end_corner_id": end_corner['id'],
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
            "length_pixels": length_pixels
        })
    
    return perimeter_model

def visualize_icf_perimeter(image, perimeter_model):
    """
    Create a clean visualization of the ICF foundation perimeter.
    
    Args:
        image: Original image.
        perimeter_model: Final perimeter model with corners and walls.
        
    Returns:
        result_image: Visualization of the foundation perimeter.
    """
    result_image = image.copy()
    
    # Extract corner points for the perimeter contour
    if not perimeter_model['corners']:
        return result_image
        
    perimeter_points = [(corner['x'], corner['y']) for corner in perimeter_model['corners']]
    
    # Create contour array for drawing
    perimeter_contour = np.array(perimeter_points).reshape(-1, 1, 2)
    
    # Draw the perimeter contour with a bold line
    cv2.drawContours(result_image, [perimeter_contour], 0, (0, 255, 0), 6)  # Thicker green line
    
    # Draw each corner
    for corner in perimeter_model['corners']:
        pt = (corner['x'], corner['y'])
        cv2.circle(result_image, pt, 10, (0, 165, 255), -1)  # Orange dot
        cv2.circle(result_image, pt, 10, (0, 0, 0), 2)       # Black outline
        
        # Add corner ID with thicker text
        text_x = corner['x'] + 15
        text_y = corner['y'] + 10
        # Draw white background for better contrast (thicker)
        cv2.putText(result_image, str(corner['id']), (text_x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 8)  # White background/outline
        # Draw text in black (thicker)
        cv2.putText(result_image, str(corner['id']), (text_x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 4)        # Black text
        
    # Draw wall measurements
    for wall in perimeter_model['walls']:
        if 'length' not in wall:
            continue
            
        # Calculate midpoint of the wall
        mid_x = (wall['start_x'] + wall['end_x']) // 2
        mid_y = (wall['start_y'] + wall['end_y']) // 2
        
        # Calculate wall angle for text placement
        angle = np.arctan2(wall['end_y'] - wall['start_y'], wall['end_x'] - wall['start_x'])
        offset_x = int(25 * np.sin(angle))
        offset_y = int(25 * np.cos(angle))
        
        # Place text label with background for clarity (thicker)
        text_pos = (mid_x + offset_x, mid_y + offset_y)
        cv2.putText(result_image, wall['length'], text_pos, 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 8)  # White outline (thicker)
        cv2.putText(result_image, wall['length'], text_pos, 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)      # Red text (thicker)
    
    return result_image

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
