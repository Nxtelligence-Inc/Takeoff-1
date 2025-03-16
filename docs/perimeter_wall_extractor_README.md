# Perimeter Wall Extractor

A tool for extracting perimeter walls from foundation plan drawings and calculating ICF-specific metrics.

## Overview

This script analyzes foundation plan drawings to:
1. Extract the perimeter walls
2. Identify corners and wall segments
3. Calculate dimensions and ICF-specific metrics
4. Generate visualization and JSON output

## Usage

```bash
python src/perimeter_wall_extractor.py <image_path> [options]
```

### Options

- `--overall_width <width>`: Specify the overall width (e.g., "38'-0"")
- `--use_llm`: Use LLM to extract dimensions from the drawing
- `--llm_type <type>`: Type of LLM to use (openai, claude) [default: openai]
- `--show_steps`: Save intermediate processing steps as images
- `--output_dir <dir>`: Output directory for result images [default: outputs]
- `--no_visualize`: Don't display the final visualization
- `--export_db`: Export results in database-ready format
- `--project_id <id>`: Project identifier for database export
- `--drawing_name <name>`: Drawing name for database export (defaults to image filename)

### Examples

Extract perimeter walls with manually specified overall width:
```bash
python src/perimeter_wall_extractor.py src/Screenshot.png --overall_width "38'-0"" --show_steps
```

Extract perimeter walls using LLM to identify dimensions:
```bash
python src/perimeter_wall_extractor.py src/Screenshot.png --use_llm --show_steps
```

## How It Works

The script follows these steps to process foundation plan drawings:

1. **Dimension Extraction** (when using `--use_llm`)
   * Sends the drawing to GPT-4o for analysis
   * Extracts overall width and wall thickness
   * Validates the extracted dimensions against the detected geometry

2. **Image Processing**
   * Enhances the drawing using contrast adjustment
   * Isolates thick walls using thresholding and morphological operations
   * Identifies the perimeter contour (largest contour in the image)

3. **Geometry Extraction**
   * Detects corners using polygon approximation
   * Creates wall segments by connecting adjacent corners
   * Calculates wall lengths in pixels

4. **Scale Calculation**
   * Uses the specified overall width to establish the scale factor
   * Converts pixel measurements to real-world dimensions (feet and inches)

5. **ICF Metrics Calculation**
   * Calculates total linear feet of walls
   * Counts total number of corners
   * Computes wall area based on standard height
   * Estimates concrete volume based on wall thickness
   * Determines bounding box dimensions

6. **Output Generation**
   * Creates visualization of the detected perimeter
   * Generates JSON file with detailed geometry and metrics
   * Includes all assumptions used in calculations

## Output

The script produces the following outputs:

1. **Visualization**: A color-coded image showing the detected perimeter walls and corners
2. **JSON Data**: A structured file containing:
   * Corner coordinates
   * Wall segments with start/end points and lengths
   * Wall thickness (if detected)
   * ICF-specific metrics with assumptions

### ICF Metrics

The JSON output includes these ICF-specific metrics:

* **Total Linear Feet**: Total length of all perimeter walls
* **Total Corners**: Number of corners in the perimeter
* **Wall Area**: Total square footage of wall area (based on standard height)
* **Concrete Volume**: Estimated cubic yards of concrete required
* **Bounding Box**: Overall width and length of the foundation
* **Assumptions**: All parameters used in calculations (wall height, form dimensions, etc.)

## Requirements

* Python 3.6+
* OpenCV
* NumPy
* Matplotlib
* python-dotenv
* OpenAI API key (if using `--use_llm` with OpenAI)
* Anthropic API key (if using `--use_llm` with Claude)
* Google Cloud Vision API credentials (for OCR functionality)

## Environment Setup

This project uses environment variables for API keys and configuration. To set up:

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file to add your API keys:
   ```
   # OpenAI API key for GPT-4o
   OPENAI_API_KEY=your-openai-api-key

   # Anthropic API key for Claude
   CLAUDE_API_KEY=your-claude-api-key

   # Google Cloud Vision API credentials
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your-project-credentials.json
   
   # Set to true to run in non-interactive mode (for background tasks)
   NON_INTERACTIVE=false
   ```

3. For Google Cloud Vision, you have two options:
   - Set `GOOGLE_APPLICATION_CREDENTIALS` to the path of your service account JSON file
   - Or set `GOOGLE_CREDENTIALS_JSON` to the actual JSON content of your service account credentials

4. For running scripts in background or automated tasks:
   - Set `NON_INTERACTIVE=true` in your .env file to prevent blocking visualizations
   - This ensures that matplotlib doesn't open interactive windows that would block execution
   - Set fallback values for when LLM extraction fails:
     ```
     DEFAULT_OVERALL_WIDTH="38'-0\""
     DEFAULT_WALL_THICKNESS="8\""
     ```
   - These fallback values are only used when `NON_INTERACTIVE=true` and LLM extraction fails
   - Without these fallback values, the script will exit if LLM extraction fails in non-interactive mode

## Database Integration

The script supports exporting results in a database-ready format, which can be useful for storing and querying foundation plan analyses. When using the `--export_db` option, the script will:

1. Create a database output directory (`outputs/database` by default)
2. Generate database-ready JSON with additional metadata (timestamp, unique ID, etc.)
3. Generate SQL statements for PostgreSQL database insertion
4. Generate payload for Supabase integration

### Database Export Examples

Export results directly to database format:
```bash
python src/perimeter_wall_extractor.py src/Screenshot.png --use_llm --export_db --project_id "project123"
```

Process existing JSON results for database storage:
```bash
python examples/prepare_for_database.py outputs/perimeter_walls.json --project_id "project123"
```

### Database Schema

The recommended database schema includes the following tables:

1. **analyses**: Core information about each analysis run
2. **icf_metrics**: ICF-specific metrics calculated for each analysis
3. **corners**: Corner coordinates for each analysis
4. **walls**: Wall segments for each analysis

For detailed information about database integration, see [docs/database_integration.md](../docs/database_integration.md).

## Notes

* For best results, use clear, high-resolution foundation plan drawings
* The LLM extraction works best when dimension lines are clearly visible at the top or bottom of the drawing
* Wall thickness detection may require clear annotations in the drawing
