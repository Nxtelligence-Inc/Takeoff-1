# Foundation Plan Analyzer

A comprehensive tool for analyzing foundation plan drawings, extracting perimeter walls, calculating ICF-specific metrics, and generating detailed material quotations for ICF construction.

![Foundation Plan Analyzer](https://via.placeholder.com/800x400?text=Foundation+Plan+Analyzer)

## Overview

This project provides a complete solution for ICF (Insulated Concrete Form) contractors and construction professionals to:

1. Extract perimeter walls from foundation plan drawings using computer vision
2. Identify corners and wall segments with precise measurements
3. Calculate dimensions and ICF-specific metrics
4. Generate detailed material quotations for ICF construction
5. Visualize foundation plans with interactive components
6. Edit and adjust wall measurements as needed

## Key Features

### Computer Vision Processing

- **LLM-Powered Dimension Extraction**: Uses GPT-4o to identify overall width and wall thickness from drawings
- **Computer Vision Processing**: Applies advanced image processing techniques to isolate and extract perimeter walls
- **Automatic Corner Detection**: Identifies foundation corners and creates a structured representation of the foundation

### ICF Metrics & Materials Calculation

- **Comprehensive ICF Metrics**: Generates key metrics for ICF construction:
  - Total linear feet of walls
  - Total number of corners
  - Wall area in square feet
  - Concrete volume in cubic yards
  - Bounding box dimensions
- **Detailed Materials Quotation**:
  - Panel requirements (standard and corner panels)
  - Rebar requirements (vertical and horizontal)
  - Concrete specifications (strength, slump, volume)
  - Accessories (form alignment, bracing, window/door bucks, fastening strips)
  - Labor estimates (crew days, pour time)
- **Customizable Calculation Settings**:
  - Adjust panel specifications (width, height, thickness)
  - Configure rebar requirements (type, spacing, courses)
  - Set concrete specifications (PSI, slump, waste factor)
  - Customize accessories and installation parameters

### Interactive Frontend

- **Foundation Plan Visualization**: Interactive visualization of detected perimeter walls and corners
- **Editable Wall Measurements**: Ability to adjust wall lengths with real-time updates to metrics
- **ICF Materials Summary**: Comprehensive breakdown of required materials with export options
- **Responsive Design**: Works on desktop and mobile devices
- **Dark/Light Mode**: Supports both dark and light themes

### System Architecture

- **Containerized Deployment**: Docker-based deployment for easy setup
- **API-First Design**: RESTful API for foundation plan analysis
- **Database Integration**: Support for PostgreSQL and Supabase
- **Scalable Architecture**: Separate frontend and backend services

## Technical Architecture

```
.
├── Frontend/                # Next.js frontend application
│   ├── app/                 # Next.js app router
│   ├── components/          # React components
│   │   ├── icf-materials-quotation.tsx  # ICF materials calculation
│   │   ├── icf-materials-summary.tsx    # Materials summary display
│   │   ├── icf-metrics-display.tsx      # ICF metrics visualization
│   │   ├── walls-table.tsx              # Editable walls table
│   │   └── foundation-plan-visualization.tsx  # Foundation visualization
│   └── public/              # Static assets and analysis results
├── src/                     # Backend Python code
│   ├── perimeter_wall_extractor.py  # Main wall extraction algorithm
│   ├── llm_module.py                # LLM integration for dimension extraction
│   ├── vision_module.py             # Computer vision utilities
│   └── api.py                       # Flask API for backend services
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile.frontend      # Frontend container definition
└── Dockerfile.backend       # Backend container definition
```

## Installation and Setup

### Prerequisites

- Python 3.6+
- Node.js 16+
- Docker and Docker Compose (for containerized deployment)
- API keys:
  - OpenAI API key (for GPT-4o dimension extraction)
  - Anthropic API key (optional, for Claude dimension extraction)
  - Google Cloud Vision API credentials (optional, for OCR functionality)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/foundation-plan-analyzer.git
   cd foundation-plan-analyzer
   ```

2. Set up the backend:
   ```bash
   # Create a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env to add your API keys
   ```

3. Set up the frontend:
   ```bash
   cd Frontend
   npm install
   ```

4. Start the development servers:
   ```bash
   # Start the backend (from the root directory)
   python src/api.py
   
   # Start the frontend (in a new terminal)
   cd Frontend
   npm run dev
   ```

5. Open your browser and navigate to `http://localhost:3000`

### Docker Deployment

For production deployment, use Docker Compose:

```bash
# Build and start the containers
docker-compose up -d

# View logs
docker-compose logs -f
```

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for detailed deployment instructions.

## Usage

### Analyzing a Foundation Plan

1. Navigate to the "Analyze" page
2. Upload a foundation plan drawing (PNG, JPG, or PDF)
3. Configure analysis settings:
   - Drawing name
   - Project
   - Wall thickness
   - Wall height
   - Analysis options (LLM dimension extraction, visualization)
4. Click "Analyze Foundation Plan"
5. View the results on the analysis details page

### Viewing and Editing Analysis Results

1. Navigate to the "Analyses" page to see all previous analyses
2. Click on an analysis to view details
3. Use the interactive visualization to see the detected perimeter
4. Edit wall measurements in the Walls tab if needed
5. View ICF metrics and materials quotation

### Generating ICF Materials Quotation

1. Open an analysis
2. Scroll to the "ICF Materials Quotation" section
3. View the materials summary or adjust calculation settings
4. Export the quotation as CSV or print it

## API Documentation

The backend provides a RESTful API for foundation plan analysis:

### Analyze Foundation Plan

```
POST /api/analyze
```

**Request Body (multipart/form-data):**
- `file`: Foundation plan image file
- `drawingName`: Name of the drawing (optional)
- `projectId`: Project identifier (optional)
- `wallThickness`: Wall thickness (e.g., "8\"")
- `wallHeight`: Wall height in feet (e.g., "8.0")
- `useLLM`: Whether to use LLM for dimension extraction (true/false)
- `visualize`: Whether to generate visualization (true/false)

**Response:**
```json
{
  "success": true,
  "analysisId": "uuid-string",
  "result": {
    "corners": [...],
    "walls": [...],
    "icf_metrics": {...},
    "metadata": {...}
  }
}
```

### Update Wall Length

```
POST /api/analyses/{id}/update-wall
```

**Request Body:**
```json
{
  "wallId": 1,
  "newLength": "12'-6\""
}
```

**Response:**
```json
{
  "success": true,
  "updatedMetrics": {
    "total_linear_feet": "120.5",
    "wall_area_sqft": "964.0",
    "concrete_volume_cuyd": "16.1"
  }
}
```

## ICF Materials Calculation

The ICF Materials Quotation component provides detailed calculations for ICF construction materials based on the foundation analysis. It includes:

### Panel Requirements

- Standard panels (count and area)
- Corner panels (count)

### Rebar Requirements

- Vertical rebar (type, count, total length)
- Horizontal rebar (type, courses, total length)

### Concrete Requirements

- Strength (PSI)
- Slump (inches)
- Volume (cubic yards)
- Volume with waste factor

### Accessories

- Form alignment systems (count)
- Bracing (count)
- Window/door bucks (linear feet)
- Fastening strips (count)

### Labor Estimates

- Crew days (3-4 person crew)
- Pour time (hours)

## Customizable Settings

The ICF Calculation Settings component allows customization of:

### Panel Specifications

- Standard panel width and height
- Form thickness
- Concrete core width

### Rebar Requirements

- Vertical rebar type and spacing
- Horizontal rebar type and courses

### Concrete Specifications

- Concrete strength (PSI)
- Concrete slump (inches)
- Waste factor (percentage)

### Accessories & Installation

- Form alignment spacing
- Bracing spacing
- Window/door bucks inclusion
- Fastening strips inclusion

## Requirements

* Python 3.6+
* OpenCV
* NumPy
* Matplotlib
* python-dotenv
* Flask
* Next.js 13+
* React 18+
* Tailwind CSS
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

* OpenAI for GPT-4o API
* OpenCV for computer vision capabilities
* Next.js and React for the frontend framework
