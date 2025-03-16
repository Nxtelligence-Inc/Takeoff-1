import { type NextRequest, NextResponse } from "next/server"
import { exec } from "child_process"
import { writeFile, readFile, mkdir } from "fs/promises"
import path from "path"
import { v4 as uuidv4 } from "uuid"

// Check if we're running in a containerized environment
const IS_CONTAINERIZED = process.env.CONTAINERIZED === "true"
const BACKEND_API_URL = process.env.BACKEND_API_URL || 'http://backend:5000'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("file") as File
    const drawingName = formData.get("drawingName") as string
    const projectId = formData.get("projectId") as string || "default_project"
    const wallThickness = formData.get("wallThickness") as string || '8"'
    const wallHeight = formData.get("wallHeight") as string || "8.0"
    const useLLM = formData.get("useLLM") === "true"
    const visualize = formData.get("visualize") === "true"

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 })
    }

    // If running in containerized environment, forward to backend API
    if (IS_CONTAINERIZED) {
      console.log("Running in containerized environment, forwarding to backend API")
      try {
        // Create a new FormData object to send to the backend
        const backendFormData = new FormData()
        backendFormData.append("file", file)
        backendFormData.append("drawingName", drawingName || "")
        backendFormData.append("projectId", projectId)
        backendFormData.append("wallThickness", wallThickness)
        backendFormData.append("wallHeight", wallHeight)
        backendFormData.append("useLLM", String(useLLM))
        backendFormData.append("visualize", String(visualize))
        
        // Forward the request to the backend API
        const response = await fetch(`${BACKEND_API_URL}/api/analyze`, {
          method: 'POST',
          body: backendFormData,
        })
        
        // Get the response from the backend
        const data = await response.json()
        
        // Return the response to the client
        if (!response.ok) {
          return NextResponse.json({ 
            error: data.error || "Backend API error", 
            details: data.details || "No details provided" 
          }, { status: response.status })
        }
        
        return NextResponse.json(data)
      } catch (error) {
        console.error("Error forwarding request to backend:", error)
        return NextResponse.json({ 
          error: "Failed to process analysis", 
          details: error instanceof Error ? error.message : String(error) 
        }, { status: 500 })
      }
    }
    
    // If not containerized, process locally (original implementation)
    console.log("Running in local environment, processing directly")
    
    // Generate unique ID for this analysis
    const analysisId = uuidv4()
    
    // Create directories if they don't exist
    const uploadsDir = path.join(process.cwd(), "public", "uploads")
    const resultsDir = path.join(process.cwd(), "public", "results", analysisId)
    await mkdir(uploadsDir, { recursive: true })
    await mkdir(resultsDir, { recursive: true })
    
    // Save the uploaded file
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)
    const uploadPath = path.join(uploadsDir, `${analysisId}.png`)
    await writeFile(uploadPath, buffer)
    
    // Build command with appropriate options
    // Use absolute paths to avoid any path resolution issues
    const rootDir = path.resolve(process.cwd(), "..")
    const pythonScript = path.join(rootDir, "src", "perimeter_wall_extractor.py")
    let command = `python "${pythonScript}" "${uploadPath}" --overall_width "38'-0" --output_dir "${resultsDir}" --no_visualize`
    
    console.log("Executing command:", command)
    
    if (useLLM) {
      command += " --use_llm"
    }
    
    if (visualize) {
      command += " --show_steps"
    }
    
    // Set environment variable for non-interactive mode
    const env = { ...process.env, NON_INTERACTIVE: "true" };
    
    // Execute Python script
    let output: string
    try {
      output = await new Promise<string>((resolve, reject) => {
        exec(command, { env }, (error, stdout, stderr) => {
          if (error) {
            console.error(`Execution error: ${error}`)
            return reject(error)
          }
          if (stderr) {
            console.error(`stderr: ${stderr}`)
          }
          resolve(stdout)
        })
      })
      
      console.log("Python script output:", output)
    } catch (error) {
      console.error("Python script execution failed:", error)
      return NextResponse.json({ 
        error: "Python script execution failed", 
        details: error instanceof Error ? error.message : String(error),
        command: command
      }, { status: 500 })
    }
    
    // Read the results
    try {
      const resultsPath = path.join(resultsDir, "perimeter_walls.json")
      const resultsData = await readFile(resultsPath, "utf8")
      const results = JSON.parse(resultsData)
      
      // Add metadata
      const metadata = {
        analysis_id: analysisId,
        timestamp: new Date().toISOString(),
        drawing_name: drawingName || file.name,
        project_id: projectId,
        wall_thickness: wallThickness,
        wall_height: wallHeight,
        image_url: `/uploads/${analysisId}.png`,
        results_url: `/results/${analysisId}/perimeter_walls.json`,
        visualization_url: `/results/${analysisId}/perimeter_walls.png`
      }
      
      // Save enhanced results with metadata
      results.metadata = metadata
      await writeFile(
        path.join(resultsDir, "analysis_results.json"),
        JSON.stringify(results, null, 2)
      )
      
      return NextResponse.json({
        success: true,
        analysisId,
        result: results
      })
    } catch (error) {
      console.error("Error reading or processing results:", error)
      return NextResponse.json({ 
        error: "Failed to read or process analysis results", 
        details: error instanceof Error ? error.message : String(error) 
      }, { status: 500 })
    }
  } catch (error) {
    console.error("Error processing analysis:", error)
    return NextResponse.json({ 
      error: "Failed to process analysis", 
      details: error instanceof Error ? error.message : String(error) 
    }, { status: 500 })
  }
}
