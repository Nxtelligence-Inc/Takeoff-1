import { NextRequest, NextResponse } from "next/server"
import { readFile, writeFile } from "fs/promises"
import path from "path"

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const analysisId = params.id
    const { wallId, newLength } = await request.json()
    
    if (!analysisId || !wallId || !newLength) {
      return NextResponse.json(
        { error: "Missing required parameters" },
        { status: 400 }
      )
    }
    
    // Read the analysis results file
    const resultsPath = path.join(
      process.cwd(),
      "public",
      "results",
      analysisId,
      "analysis_results.json"
    )
    
    const data = await readFile(resultsPath, "utf8")
    const analysisData = JSON.parse(data)
    
    // Find and update the wall
    const wallIndex = analysisData.walls.findIndex((wall: any) => wall.id === wallId)
    
    if (wallIndex === -1) {
      return NextResponse.json(
        { error: `Wall with ID ${wallId} not found` },
        { status: 404 }
      )
    }
    
    // Update the wall length
    analysisData.walls[wallIndex].length = newLength
    
    // Recalculate ICF metrics if they exist
    if (analysisData.icf_metrics) {
      // Convert all wall lengths to inches
      let totalLinearFeet = 0
      
      for (const wall of analysisData.walls) {
        // Parse feet and inches
        const lengthStr = wall.length
        const cleaned = lengthStr.replace(/\\"/g, '"').replace(/"/g, '"')
        const parts = cleaned.split("'")
        const feet = parseInt(parts[0], 10)
        
        let inches = 0
        if (parts.length > 1) {
          const inchPart = parts[1].replace(/"/g, '').trim()
          if (inchPart && inchPart !== '0') {
            inches = parseInt(inchPart, 10)
          }
        }
        
        // Convert to decimal feet
        const lengthInFeet = feet + (inches / 12)
        totalLinearFeet += lengthInFeet
      }
      
      // Update ICF metrics
      analysisData.icf_metrics.total_linear_feet = totalLinearFeet.toFixed(1)
      
      // Update wall area
      const wallHeight = parseFloat(analysisData.icf_metrics.assumptions.wall_height_feet)
      analysisData.icf_metrics.wall_area_sqft = (totalLinearFeet * wallHeight).toFixed(1)
      
      // Update concrete volume
      const wallThicknessFeet = parseFloat(analysisData.icf_metrics.wall_thickness_feet)
      const concreteCuFt = totalLinearFeet * wallHeight * wallThicknessFeet
      analysisData.icf_metrics.concrete_volume_cuyd = (concreteCuFt / 27).toFixed(1)
    }
    
    // Save the updated data
    await writeFile(resultsPath, JSON.stringify(analysisData, null, 2))
    
    return NextResponse.json({
      success: true,
      message: `Wall ${wallId} updated successfully`,
      updatedWall: analysisData.walls[wallIndex],
      updatedMetrics: analysisData.icf_metrics
    })
  } catch (error) {
    console.error("Error updating wall:", error)
    return NextResponse.json(
      { error: "Failed to update wall", details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    )
  }
}
