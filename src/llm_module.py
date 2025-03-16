#!/usr/bin/env python3
import os
import re
import json
import base64
import copy
from typing import Dict, Any, Optional, List, Union, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import pydantic or define fallback classes
try:
    from pydantic import BaseModel, Field  # type: ignore
    HAS_PYDANTIC = True
except ImportError:
    print("Warning: Pydantic package not installed. Structured outputs will not work properly.")
    HAS_PYDANTIC = False
    
    # Define fallback classes if pydantic is not available
    def Field(default=None, **kwargs):
        return default
    
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        @classmethod
        def model_json_schema(cls):
            return {}

# Define the Pydantic model for foundation dimensions
class FoundationDimensions(BaseModel):  # type: ignore
    overall_width: Optional[str] = Field(None, description="Overall width of the structure in feet and inches format (e.g., '38'-0\"')")  # type: ignore
    wall_thickness: Optional[str] = Field(None, description="Wall thickness in inches format (e.g., '8\"')")  # type: ignore
    confidence: int = Field(0, description="Confidence score from 0-100")  # type: ignore
    explanation: str = Field("", description="Explanation of how dimensions were identified")  # type: ignore

try:
    import openai
except ImportError:
    print("Warning: OpenAI package not installed. GPT-4o features will not work.")
    openai = None

try:
    # Import Anthropic for Claude API
    from anthropic import Anthropic, AnthropicError
except ImportError:
    print("Warning: Anthropic package not installed. Claude features will not work.")
    Anthropic = None
    AnthropicError = Exception  # Fallback for type checking

# --- LLM Interaction Functions ---
def call_openai_llm(prompt: str, image_base64: str, api_key: Optional[str] = None) -> str:
    """Calls the OpenAI GPT-4o API with the given prompt and image."""
    if openai is None:
        return "Error: OpenAI library not installed."
    
    # Use provided API key or get from environment
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "Error: No OpenAI API key provided. Set OPENAI_API_KEY environment variable or pass api_key parameter."
    
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
        # Ensure we return a string
        content = response.choices[0].message.content
        if content is None:
            return "Error: Empty response from OpenAI API"
        return content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return f"Error: {e}"

def call_claude_llm(prompt: str, image_base64: str, api_key: Optional[str] = None) -> str:
    """Calls the Anthropic Claude 3.7 Sonnet API with the given prompt and image."""
    if Anthropic is None:
        return "Error: Anthropic library not installed."
    
    # Use provided API key or get from environment
    api_key = api_key or os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        return "Error: No Claude API key provided. Set CLAUDE_API_KEY environment variable or pass api_key parameter."
    
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
        # Handle the response safely
        try:
            # Extract text from the response
            if hasattr(response, 'content') and response.content:
                # Access the first content item's text
                content_item = response.content[0] if response.content else None
                content_text = None
                
                # Try to get text content in a way that works with different response structures
                if content_item:
                    # Try direct attribute access first
                    if hasattr(content_item, 'text'):
                        content_text = getattr(content_item, 'text')  # type: ignore
                    # Try dictionary-style access as fallback
                    elif hasattr(content_item, 'get') and callable(getattr(content_item, 'get')):
                        content_text = content_item.get('text')  # type: ignore
                    # Try direct string conversion as last resort
                    elif hasattr(content_item, '__str__'):
                        content_text = str(content_item)
                    if content_text is not None:
                        return str(content_text)
            
            # If we couldn't extract text using the expected structure
            return "Error: Could not extract text from Claude API response"
        except Exception as e:
            print(f"Error extracting text from Claude response: {e}")
            return f"Error processing Claude response: {e}"
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return f"Error: {e}"

def parse_llm_response(response_text: str) -> Dict[str, Any]:
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
    
def create_prompt(ocr_results: List[Dict[str, Any]], overall_width_inches: float, 
                 geometry_data: Optional[Dict[str, Any]] = None, 
                 image_base64: Optional[str] = None) -> str:
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

def create_perimeter_prompt(geometry_data: Dict[str, Any], overall_width_inches: float) -> str:
    """
    Creates a prompt focused on foundation perimeter analysis for ICF construction.
    
    Args:
        geometry_data: Dictionary containing corner coordinates.
        overall_width_inches: Width of the foundation in inches.
        
    Returns:
        prompt: Prompt for the LLM.
    """
    prompt = f"""You are an expert at analyzing architectural foundation plans for Insulated Concrete Form (ICF) construction.

I have detected {len(geometry_data['corners'])} potential corner points on a foundation plan.
Each point has a yellow dot with a number label.

The foundation has an overall width of {overall_width_inches} inches ({overall_width_inches/12:.1f} feet).

Your task is to:
1. Identify which numbered points represent actual foundation perimeter corners
2. Specify the order to connect these points to form the complete foundation perimeter

IMPORTANT INSTRUCTIONS:
- Include ALL corners that form the complete exterior foundation perimeter
- Include corners that are part of detailed areas like entrances, porches, or steps as long as they form part of the foundation wall perimeter
- For ICF construction, we need the precise outer shape of the foundation including all jogs, steps, and detailed areas
- Points that don't represent foundation corners may be dimension markers, text, or other drawing elements
- The shape is likely rectilinear with corners at approximately 90° angles

Here is the corner data:
```json
{json.dumps(geometry_data, indent=2)}
```

Format your response as a JSON object with the following structure:
```json
{{
  "perimeter_corner_ids": [0, 4, 5, 9, 12, 15],  # IDs of points that form the perimeter, in connection order
  "explanation": "I identified these corners because..."
}}
```

The perimeter_corner_ids should begin at any corner and proceed in either clockwise or counterclockwise order around the entire perimeter.
"""
    return prompt

def create_corner_correction_prompt(geometry_data: Dict[str, Any]) -> str:
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

def create_llm_feedback_prompt(image_base64: str, geometry_data: Optional[Dict[str, Any]] = None) -> str:
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

def extract_dimensions_with_llm(image_path: str, api_key: Optional[str] = None, llm_type: str = "openai") -> Dict[str, Any]:
    """
    Extract overall width and wall thickness from a foundation drawing using LLM.
    
    Args:
        image_path: Path to the foundation plan image.
        api_key: Optional API key for the LLM. If not provided, will use environment variables.
        llm_type: Type of LLM to use (openai, claude).
        
    Returns:
        dimensions: Dictionary with overall_width and wall_thickness.
    """
    print("\n--- Extracting Dimensions with LLM ---")
    
    # Read and encode the image
    try:
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
    except Exception as e:
        print(f"Error reading image file: {e}")
        return {"error": f"Failed to read image file: {e}"}
    
    # Create a detailed and guided prompt
    prompt = """
    You are an expert architectural drawing analyst specializing in foundation plans. Your ONLY task is to extract the EXACT overall width and wall thickness from this foundation drawing.

    CRITICAL INSTRUCTIONS FOR FINDING OVERALL WIDTH:
    1. The overall width is ALWAYS shown as the LARGEST dimension at the VERY TOP or VERY BOTTOM of the drawing
    2. Look for dimension lines with arrows at both ends that span the ENTIRE width of the structure
    3. These dimension lines are typically placed outside the perimeter of the building
    4. The overall width is the largest horizontal measurement that spans from the leftmost to rightmost exterior walls
    5. Look for text labels like "38'-0\"" adjacent to these dimension lines
    6. IGNORE all interior dimensions, partial measurements, or dimensions not at the extreme top or bottom
    7. If you see multiple width dimensions, ONLY consider the ones at the very top or very bottom edge of the drawing

    CRITICAL INSTRUCTIONS FOR FINDING WALL THICKNESS:
    1. Look for small dimension lines between parallel lines representing walls
    2. Look for text annotations like "8\" WALL" or "8\" THICK WALL"
    3. Look for wall cross-sections that show the thickness
    4. Common foundation wall thicknesses are 6", 8", 10", or 12"

    IMPORTANT: If you cannot find the exact overall width with high confidence, set the confidence score below 50 and explain why.

    Provide your response in the following JSON format:
    ```json
    {
      "overall_width": "38'-0\"",  // Format as feet and inches with quotes, or null if not found
      "wall_thickness": "8\"",     // Format as inches with quotes, or null if not found
      "confidence": 90,            // 0-100 confidence score
      "explanation": "I found the overall width dimension line at the very bottom of the drawing marked as 38'-0\". The wall thickness is shown in a detail as 8\"."
    }
    ```
    """
    
    # Get API key based on LLM type
    if not api_key:
        if llm_type == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
        elif llm_type == "claude":
            api_key = os.environ.get("CLAUDE_API_KEY")
    
    # Check if we have an API key
    if not api_key:
        print(f"Error: No API key provided for {llm_type}")
        return {"error": f"No API key provided for {llm_type}. Set {llm_type.upper()}_API_KEY environment variable or pass api_key parameter."}
    
    # For OpenAI with structured outputs
    if llm_type == "openai" and openai is not None:
        try:
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1000
            )
            # Parse the response
            content = response.choices[0].message.content
            if content is None:
                return {"error": "Empty response from OpenAI API"}
            
            # Parse JSON response
            try:
                dimensions = json.loads(content)
                print(f"Extracted dimensions: {json.dumps(dimensions, indent=2)}")
                return dimensions
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {e}")
                print(f"Raw response: {content}")
                return {"error": f"Failed to parse JSON response: {e}", "raw_response": content}
                
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return {"error": f"{e}"}
    
    # For standard LLM calls (without structured outputs)
    if llm_type == "openai":
        llm_response = call_openai_llm(prompt, base64_image, api_key)
    elif llm_type == "claude":
        llm_response = call_claude_llm(prompt, base64_image, api_key)
    else:
        return {"error": f"Unsupported LLM type: {llm_type}"}
    
    # Parse the response
    dimensions = parse_llm_response(llm_response)
    
    # Validate the response
    if not dimensions:
        print("Warning: LLM failed to extract dimensions properly")
        print(f"Raw LLM response: {llm_response}")
        return {"error": "Failed to extract dimensions", "raw_response": llm_response}
    
    # Check confidence level for overall width
    if "overall_width" not in dimensions or dimensions["overall_width"] is None:
        dimensions["overall_width"] = None
        dimensions["overall_width_confidence"] = 0
    elif "confidence" in dimensions and dimensions["confidence"] < 50:
        # Low confidence, treat as not found
        dimensions["overall_width_confidence"] = dimensions["confidence"]
        dimensions["overall_width"] = None
    else:
        dimensions["overall_width_confidence"] = dimensions.get("confidence", 75)
    
    print(f"Extracted dimensions: {json.dumps(dimensions, indent=2)}")
    return dimensions

def validate_dimensions(dimensions: Dict[str, Any], image_path: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validate extracted dimensions against the detected geometry.
    
    Args:
        dimensions: Dictionary with overall_width and wall_thickness.
        image_path: Path to the foundation plan image.
        
    Returns:
        is_valid: Boolean indicating if dimensions are valid.
        message: Validation message.
        validated_dimensions: Potentially corrected dimensions.
    """
    from typing import Tuple
    
    validated_dimensions = dimensions.copy()
    
    # Check if overall width is present
    if not dimensions.get("overall_width"):
        return False, "No overall width found", validated_dimensions
    
    # Convert to inches
    try:
        from vision_module import feet_inches_to_inches
    except ImportError:
        # Define a local version if import fails
        def feet_inches_to_inches(feet_str):
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
    
    overall_width_inches = feet_inches_to_inches(dimensions["overall_width"])
    if not overall_width_inches:
        return False, f"Invalid overall width format: {dimensions['overall_width']}", validated_dimensions
    
    # Load the image to get its dimensions
    try:
        import cv2
        import numpy as np
        
        image = cv2.imread(image_path)
        if image is None:
            return False, f"Could not open image: {image_path}", validated_dimensions
            
        # Extract perimeter walls to get geometry data
        try:
            # Try to import and use the extract_perimeter_walls function
            # This is a bit circular but helps with validation
            import sys
            import os
            
            # Get the directory of the current file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Add the directory to sys.path if it's not already there
            if current_dir not in sys.path:
                sys.path.append(current_dir)
            
            # Now try to import the function
            try:
                from perimeter_wall_extractor import extract_perimeter_walls
                
                _, geometry_data, _ = extract_perimeter_walls(image_path, show_steps=False)
                
                # Find the longest wall in pixels
                longest_wall_length = 0
                for wall in geometry_data['walls']:
                    if wall['length_pixels'] > longest_wall_length:
                        longest_wall_length = wall['length_pixels']
                
                if longest_wall_length == 0:
                    return False, "Could not detect any walls", validated_dimensions
                    
                # Calculate the implied scale factor
                scale_factor = overall_width_inches / longest_wall_length
                
                # Check if scale factor is reasonable (e.g., between 0.1 and 30 inches per pixel)
                if not (0.1 <= scale_factor <= 30):
                    return False, f"Unreasonable scale factor: {scale_factor:.4f} inches per pixel", validated_dimensions
                    
                print(f"Validation: Scale factor is {scale_factor:.4f} inches per pixel (reasonable range: 0.1-30)")
                return True, "Dimensions validated successfully", validated_dimensions
                
            except (ImportError, Exception) as e:
                print(f"Warning: Could not validate against geometry: {e}")
                # Fall back to basic image dimension check
        except Exception as e:
            print(f"Warning: Could not validate against geometry: {e}")
            # Fall back to basic image dimension check
            
        # Get image dimensions
        height, width = image.shape[:2]
        
        # Estimate a reasonable scale factor range based on image size
        # Assuming the drawing represents a structure between 20 and 200 feet wide
        min_scale = 20 * 12 / width  # 20 feet in inches / width in pixels
        max_scale = 200 * 12 / width  # 200 feet in inches / width in pixels
        
        # Calculate implied scale factor
        implied_scale = overall_width_inches / width
        
        if not (min_scale <= implied_scale <= max_scale):
            return False, f"Suspicious overall width: {dimensions['overall_width']} implies {implied_scale:.4f} inches per pixel (expected range: {min_scale:.4f}-{max_scale:.4f})", validated_dimensions
        
        return True, "Dimensions passed basic validation", validated_dimensions
            
    except Exception as e:
        print(f"Validation error: {e}")
        return False, f"Could not validate dimensions: {e}", validated_dimensions

def correct_corners_with_llm(geometry_data: Dict[str, Any], image_base64: str, 
                           api_key: Optional[str] = None, llm_type: str = "openai") -> Dict[str, Any]:
    """
    Uses an LLM to correct corner positions to form 90° angles.
    
    Args:
        geometry_data: Dictionary containing corner coordinates and wall segments.
        image_base64: Base64-encoded image for visual context.
        api_key: Optional API key for the LLM. If not provided, will use environment variables.
        llm_type: Type of LLM to use (openai, claude).
        
    Returns:
        corrected_geometry: Updated geometry data with corrected corner positions.
    """
    print("\n--- Correcting Corner Positions with LLM ---")
    
    # Create the prompt
    prompt = create_corner_correction_prompt(geometry_data)
    
    # Get API key based on LLM type
    if not api_key:
        if llm_type == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
        elif llm_type == "claude":
            api_key = os.environ.get("CLAUDE_API_KEY")
    
    # Check if we have an API key
    if not api_key:
        print(f"Error: No API key provided for {llm_type}")
        return geometry_data
        
    if llm_type == "openai":
        llm_response = call_openai_llm(prompt, image_base64, api_key)
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
    import numpy as np
    for wall in corrected_geometry['walls']:
        start_x = wall['start_x']
        start_y = wall['start_y']
        end_x = wall['end_x']
        end_y = wall['end_y']
        
        # Calculate wall length in pixels
        wall['length_pixels'] = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
    
    return corrected_geometry
