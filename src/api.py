from flask import Flask, request, jsonify
import os
import uuid
import json
import datetime
import subprocess
from pathlib import Path

app = Flask(__name__)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        # Check if file is in the request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        drawing_name = request.form.get('drawingName', '')
        project_id = request.form.get('projectId', 'default_project')
        wall_thickness = request.form.get('wallThickness', '8"')
        wall_height = request.form.get('wallHeight', '8.0')
        use_llm = request.form.get('useLLM', 'false') == 'true'
        visualize = request.form.get('visualize', 'true') == 'true'
        
        # Generate unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        
        # Create directories if they don't exist
        uploads_dir = Path('/app/public/uploads')
        results_dir = Path(f'/app/public/results/{analysis_id}')
        uploads_dir.mkdir(exist_ok=True, parents=True)
        results_dir.mkdir(exist_ok=True, parents=True)
        
        # Save the uploaded file
        upload_path = uploads_dir / f"{analysis_id}.png"
        file.save(upload_path)
        
        # Build command with appropriate options
        python_script = Path('/app/src/perimeter_wall_extractor.py')
        command = [
            'python', 
            str(python_script), 
            str(upload_path), 
            '--overall_width', 
            "38'-0", 
            '--output_dir', 
            str(results_dir), 
            '--no_visualize'
        ]
        
        if use_llm:
            command.append('--use_llm')
        
        if visualize:
            command.append('--show_steps')
        
        # Execute Python script
        env = os.environ.copy()
        env['NON_INTERACTIVE'] = 'true'
        
        process = subprocess.run(command, env=env, capture_output=True, text=True)
        
        if process.returncode != 0:
            return jsonify({
                "error": "Python script execution failed",
                "details": process.stderr,
                "command": ' '.join(command)
            }), 500
        
        # Read the results
        results_path = results_dir / "perimeter_walls.json"
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        # Add metadata
        metadata = {
            "analysis_id": analysis_id,
            "timestamp": str(datetime.datetime.now().isoformat()),
            "drawing_name": drawing_name or file.filename,
            "project_id": project_id,
            "wall_thickness": wall_thickness,
            "wall_height": wall_height,
            "image_url": f"/uploads/{analysis_id}.png",
            "results_url": f"/results/{analysis_id}/perimeter_walls.json",
            "visualization_url": f"/results/{analysis_id}/perimeter_walls.png"
        }
        
        # Save enhanced results with metadata
        results["metadata"] = metadata
        with open(results_dir / "analysis_results.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        return jsonify({
            "success": True,
            "analysisId": analysis_id,
            "result": results
        })
    
    except Exception as e:
        return jsonify({
            "error": "Failed to process analysis",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
