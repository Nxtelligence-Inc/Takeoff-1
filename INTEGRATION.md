# Python Backend and Next.js Frontend Integration

This document describes the integration between the Python backend (`/src`) and the Next.js frontend (`/Frontend`) for the Foundation Plan Analyzer project.

## Integration Overview

The integration uses a file-based approach to communicate between the Python backend and Next.js frontend:

1. The frontend uploads foundation plan images to the `/public/uploads` directory
2. The Next.js API route executes the Python script as a child process
3. The Python script processes the image and saves results to the `/public/results` directory
4. The frontend reads the results from the `/public/results` directory and displays them

This approach avoids the need for a separate API server or database, making it simpler to deploy and maintain for demo purposes.

## Directory Structure

```
/DrawingOCR
  /src                      # Python backend
    perimeter_wall_extractor.py
    vision_module.py
    llm_module.py
    database_utils.py
  
  /Frontend                 # Next.js frontend
    /app
      /api
        /analyze            # API endpoint for analysis
          route.ts
    /public
      /uploads              # Store uploaded images
      /results              # Store analysis results
    /components             # UI components
```

## Integration Components

### 1. File Upload Component (`/Frontend/components/file-uploader.tsx`)

- Handles file selection and preview
- Submits the file to the API endpoint with analysis parameters
- Shows loading state during analysis
- Redirects to the results page when analysis is complete

### 2. API Route (`/Frontend/app/api/analyze/route.ts`)

- Receives the uploaded file and analysis parameters
- Saves the file to the `/public/uploads` directory
- Executes the Python script as a child process
- Reads the results from the output directory
- Returns the analysis ID and results to the frontend

### 3. Python Script Execution

The API route executes the Python script with the following command:

```javascript
const command = `python "${pythonScript}" "${uploadPath}" --overall_width "38'-0\"" --output_dir "${resultsDir}"`;
```

Additional parameters like `--use_llm` and `--show_steps` are added based on user settings.

### 4. Results Storage

The Python script saves the analysis results to the specified output directory:

- `perimeter_walls.json`: Contains the extracted perimeter walls, corners, and ICF metrics
- `perimeter_walls.png`: Visualization of the detected perimeter walls

The API route adds metadata to the results and saves an enhanced version:

- `analysis_results.json`: Contains the original results plus metadata like timestamp, drawing name, etc.

### 5. Results Display

The frontend reads the analysis results from the `/public/results` directory:

- The analysis detail page (`/Frontend/app/analyses/[id]/page.tsx`) reads `analysis_results.json`
- The visualization component (`/Frontend/components/foundation-plan-visualization.tsx`) displays the visualization image or renders the results on a canvas

## Data Flow

1. User uploads a foundation plan image on the analyze page
2. Frontend sends the image to the API endpoint
3. API endpoint saves the image and executes the Python script
4. Python script processes the image and saves results
5. API endpoint reads the results and returns them to the frontend
6. Frontend redirects to the analysis detail page
7. Analysis detail page reads the results and displays them

## Error Handling

- The API endpoint catches and returns errors from the Python script
- The frontend displays error messages to the user
- The file uploader component shows loading state during analysis

## Future Improvements

- Add authentication to secure the API endpoint
- Implement a proper database for storing analysis results
- Add progress indicators for long-running analyses
- Implement file cleanup to remove old uploads and results
