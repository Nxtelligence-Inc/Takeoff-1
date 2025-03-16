#!/usr/bin/env python3
"""
Database Utilities for Foundation Plan Analyzer

This module provides utilities for preparing the output data for database storage
and integration with PostgreSQL or Supabase.

It includes:
- Functions to format output data for database insertion
- Helper functions for generating SQL statements
- Supabase integration utilities
"""

import json
import uuid
import datetime
import os
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def generate_analysis_id() -> str:
    """
    Generate a unique identifier for an analysis run.
    
    Returns:
        A unique string identifier (UUID)
    """
    return str(uuid.uuid4())


def add_metadata(data: Dict[str, Any], 
                 drawing_name: Optional[str] = None,
                 project_id: Optional[str] = None,
                 user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Add metadata to the analysis results for database storage.
    
    Args:
        data: The original analysis data
        drawing_name: Optional name of the drawing
        project_id: Optional project identifier
        user_id: Optional user identifier
        
    Returns:
        Enhanced data dictionary with metadata
    """
    # Create a copy to avoid modifying the original
    enhanced_data = data.copy()
    
    # Add metadata
    enhanced_data["metadata"] = {
        "analysis_id": generate_analysis_id(),
        "timestamp": datetime.datetime.now().isoformat(),
        "drawing_name": drawing_name,
        "project_id": project_id,
        "user_id": user_id
    }
    
    return enhanced_data


def normalize_numeric_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert string numeric values to actual numeric types for database storage.
    
    Args:
        data: The analysis data with string numeric values
        
    Returns:
        Data with numeric values converted to appropriate types
    """
    normalized = data.copy()
    
    # Process ICF metrics
    if "icf_metrics" in normalized:
        metrics = normalized["icf_metrics"]
        
        # Convert string values to float where appropriate
        if "total_linear_feet" in metrics:
            metrics["total_linear_feet"] = float(metrics["total_linear_feet"])
            
        if "wall_area_sqft" in metrics:
            metrics["wall_area_sqft"] = float(metrics["wall_area_sqft"])
            
        if "wall_thickness_feet" in metrics:
            metrics["wall_thickness_feet"] = float(metrics["wall_thickness_feet"])
            
        if "concrete_volume_cuyd" in metrics:
            metrics["concrete_volume_cuyd"] = float(metrics["concrete_volume_cuyd"])
            
        # Process bounding box
        if "bounding_box" in metrics:
            if "width_feet" in metrics["bounding_box"]:
                metrics["bounding_box"]["width_feet"] = float(metrics["bounding_box"]["width_feet"])
                
            if "length_feet" in metrics["bounding_box"]:
                metrics["bounding_box"]["length_feet"] = float(metrics["bounding_box"]["length_feet"])
    
    # Process walls
    if "walls" in normalized:
        for wall in normalized["walls"]:
            if "length_pixels" in wall:
                # Ensure length_pixels is float
                wall["length_pixels"] = float(wall["length_pixels"])
    
    return normalized


def prepare_for_database(data: Dict[str, Any], 
                         drawing_name: Optional[str] = None,
                         project_id: Optional[str] = None,
                         user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Prepare analysis data for database storage by adding metadata and normalizing values.
    
    Args:
        data: The original analysis data
        drawing_name: Optional name of the drawing
        project_id: Optional project identifier
        user_id: Optional user identifier
        
    Returns:
        Database-ready data
    """
    # Add metadata
    enhanced_data = add_metadata(data, drawing_name, project_id, user_id)
    
    # Normalize numeric values
    normalized_data = normalize_numeric_values(enhanced_data)
    
    return normalized_data


def generate_postgresql_statements(data: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate PostgreSQL INSERT statements for the analysis data.
    
    Args:
        data: The prepared analysis data
        
    Returns:
        Dictionary of SQL statements for different tables
    """
    # Ensure data has been prepared for database
    if "metadata" not in data:
        data = prepare_for_database(data)
    
    analysis_id = data["metadata"]["analysis_id"]
    timestamp = data["metadata"]["timestamp"]
    drawing_name = data["metadata"]["drawing_name"] or "unnamed_drawing"
    project_id = data["metadata"]["project_id"]
    user_id = data["metadata"]["user_id"]
    
    # Initialize SQL statements dictionary
    sql_statements = {}
    
    # Analysis table
    analysis_sql = f"""
    INSERT INTO analyses (
        id, timestamp, drawing_name, project_id, user_id, 
        wall_thickness, raw_data
    ) VALUES (
        '{analysis_id}', 
        '{timestamp}', 
        '{drawing_name}', 
        {f"'{project_id}'" if project_id else "NULL"}, 
        {f"'{user_id}'" if user_id else "NULL"}, 
        {f"'{data.get('wall_thickness', 'unknown')}'"}, 
        '{json.dumps(data)}'::jsonb
    );
    """
    sql_statements["analyses"] = analysis_sql
    
    # ICF Metrics table
    if "icf_metrics" in data:
        metrics = data["icf_metrics"]
        metrics_sql = f"""
        INSERT INTO icf_metrics (
            analysis_id, total_linear_feet, total_corners, wall_area_sqft,
            wall_thickness_feet, concrete_volume_cuyd, 
            bounding_box_width_feet, bounding_box_length_feet
        ) VALUES (
            '{analysis_id}',
            {metrics.get('total_linear_feet', 'NULL')},
            {metrics.get('total_corners', 'NULL')},
            {metrics.get('wall_area_sqft', 'NULL')},
            {metrics.get('wall_thickness_feet', 'NULL')},
            {metrics.get('concrete_volume_cuyd', 'NULL')},
            {metrics.get('bounding_box', {}).get('width_feet', 'NULL')},
            {metrics.get('bounding_box', {}).get('length_feet', 'NULL')}
        );
        """
        sql_statements["icf_metrics"] = metrics_sql
    
    # Corners table
    if "corners" in data:
        corners_sql = []
        for corner in data["corners"]:
            corner_sql = f"""
            INSERT INTO corners (
                analysis_id, corner_id, x, y
            ) VALUES (
                '{analysis_id}',
                {corner.get('id', 'NULL')},
                {corner.get('x', 'NULL')},
                {corner.get('y', 'NULL')}
            );
            """
            corners_sql.append(corner_sql)
        sql_statements["corners"] = "\n".join(corners_sql)
    
    # Walls table
    if "walls" in data:
        walls_sql = []
        for wall in data["walls"]:
            wall_sql = f"""
            INSERT INTO walls (
                analysis_id, wall_id, start_corner_id, end_corner_id,
                start_x, start_y, end_x, end_y, 
                length_pixels, length
            ) VALUES (
                '{analysis_id}',
                {wall.get('id', 'NULL')},
                {wall.get('start_corner_id', 'NULL')},
                {wall.get('end_corner_id', 'NULL')},
                {wall.get('start_x', 'NULL')},
                {wall.get('start_y', 'NULL')},
                {wall.get('end_x', 'NULL')},
                {wall.get('end_y', 'NULL')},
                {wall.get('length_pixels', 'NULL')},
                '{wall.get('length', 'unknown')}'
            );
            """
            walls_sql.append(wall_sql)
        sql_statements["walls"] = "\n".join(walls_sql)
    
    return sql_statements


def generate_supabase_payload(data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate Supabase-ready payload for the analysis data.
    
    Args:
        data: The prepared analysis data
        
    Returns:
        Dictionary of table names and their respective records
    """
    # Ensure data has been prepared for database
    if "metadata" not in data:
        data = prepare_for_database(data)
    
    analysis_id = data["metadata"]["analysis_id"]
    
    # Initialize payload
    payload = {
        "analyses": [],
        "icf_metrics": [],
        "corners": [],
        "walls": []
    }
    
    # Analysis record
    analysis_record = {
        "id": analysis_id,
        "timestamp": data["metadata"]["timestamp"],
        "drawing_name": data["metadata"]["drawing_name"],
        "project_id": data["metadata"]["project_id"],
        "user_id": data["metadata"]["user_id"],
        "wall_thickness": data.get("wall_thickness"),
        "raw_data": data
    }
    payload["analyses"].append(analysis_record)
    
    # ICF Metrics record
    if "icf_metrics" in data:
        metrics = data["icf_metrics"]
        metrics_record = {
            "analysis_id": analysis_id,
            "total_linear_feet": metrics.get("total_linear_feet"),
            "total_corners": metrics.get("total_corners"),
            "wall_area_sqft": metrics.get("wall_area_sqft"),
            "wall_thickness_feet": metrics.get("wall_thickness_feet"),
            "concrete_volume_cuyd": metrics.get("concrete_volume_cuyd"),
            "bounding_box_width_feet": metrics.get("bounding_box", {}).get("width_feet"),
            "bounding_box_length_feet": metrics.get("bounding_box", {}).get("length_feet")
        }
        payload["icf_metrics"].append(metrics_record)
    
    # Corner records
    if "corners" in data:
        for corner in data["corners"]:
            corner_record = {
                "analysis_id": analysis_id,
                "corner_id": corner.get("id"),
                "x": corner.get("x"),
                "y": corner.get("y")
            }
            payload["corners"].append(corner_record)
    
    # Wall records
    if "walls" in data:
        for wall in data["walls"]:
            wall_record = {
                "analysis_id": analysis_id,
                "wall_id": wall.get("id"),
                "start_corner_id": wall.get("start_corner_id"),
                "end_corner_id": wall.get("end_corner_id"),
                "start_x": wall.get("start_x"),
                "start_y": wall.get("start_y"),
                "end_x": wall.get("end_x"),
                "end_y": wall.get("end_y"),
                "length_pixels": wall.get("length_pixels"),
                "length": wall.get("length")
            }
            payload["walls"].append(wall_record)
    
    return payload


def save_database_ready_json(data: Dict[str, Any], output_path: str) -> None:
    """
    Save database-ready JSON to a file.
    
    Args:
        data: The prepared analysis data
        output_path: Path to save the JSON file
    """
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Database-ready JSON saved to {output_path}")


def batch_process_results(result_files: List[str], 
                          output_dir: str = "outputs/database",
                          project_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process multiple result files for batch database insertion.
    
    Args:
        result_files: List of paths to result JSON files
        output_dir: Directory to save the database-ready files
        project_id: Optional project identifier
        
    Returns:
        Summary of processed files
    """
    import os
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    summary = {
        "processed_files": [],
        "failed_files": [],
        "total_processed": 0,
        "total_failed": 0
    }
    
    # Process each file
    for file_path in result_files:
        try:
            # Extract drawing name from file path
            drawing_name = os.path.basename(file_path).replace(".json", "")
            
            # Load the data
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Prepare for database
            db_ready_data = prepare_for_database(data, drawing_name, project_id)
            
            # Save database-ready JSON
            output_path = os.path.join(output_dir, f"{drawing_name}_db_ready.json")
            save_database_ready_json(db_ready_data, output_path)
            
            # Add to summary
            summary["processed_files"].append({
                "original_path": file_path,
                "db_ready_path": output_path,
                "analysis_id": db_ready_data["metadata"]["analysis_id"]
            })
            summary["total_processed"] += 1
            
        except Exception as e:
            # Add to failed files
            summary["failed_files"].append({
                "path": file_path,
                "error": str(e)
            })
            summary["total_failed"] += 1
    
    # Save summary
    summary_path = os.path.join(output_dir, "batch_process_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary
