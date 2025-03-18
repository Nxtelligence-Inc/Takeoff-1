import { NextRequest, NextResponse } from "next/server";
import { readFile } from "fs/promises";
import path from "path";

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const id = params.id;
    
    // Check if we're running in a containerized environment
    const IS_CONTAINERIZED = process.env.CONTAINERIZED === "true";
    
    // Define paths for both containerized and local environments
    let resultsPath;
    let possiblePaths = [];
    
    if (IS_CONTAINERIZED) {
      // In containerized environment, try multiple possible locations
      possiblePaths = [
        path.join("/app/public/results", id, "analysis_results.json"),
        path.join("/app/results", id, "analysis_results.json"),
        path.join(process.cwd(), "public", "results", id, "analysis_results.json")
      ];
    } else {
      // In local environment, try multiple possible locations
      possiblePaths = [
        path.join(process.cwd(), "public", "results", id, "analysis_results.json"),
        path.join(process.cwd(), "..", "public", "results", id, "analysis_results.json"),
        path.join(process.cwd(), "Frontend", "public", "results", id, "analysis_results.json")
      ];
    }
    
    // Try each path until we find the file
    let fileFound = false;
    for (const testPath of possiblePaths) {
      try {
        await readFile(testPath, "utf8");
        resultsPath = testPath;
        fileFound = true;
        console.log(`Found analysis results at: ${resultsPath}`);
        break;
      } catch (error) {
        console.log(`File not found at: ${testPath}`);
      }
    }
    
    if (!fileFound) {
      console.error(`Could not find analysis results for ID ${id} in any location`);
      return NextResponse.json(
        { error: "Analysis results not found" },
        { status: 404 }
      );
    }
    
    try {
      // Read the analysis results file
      if (!resultsPath) {
        throw new Error("Results path is undefined");
      }
      const data = await readFile(resultsPath, "utf8");
      const results = JSON.parse(data);
      
      return NextResponse.json(results);
    } catch (error) {
      console.error(`Error reading analysis results for ID ${id}:`, error);
      return NextResponse.json(
        { error: "Analysis results not found" },
        { status: 404 }
      );
    }
  } catch (error) {
    console.error("Error in analysis results API route:", error);
    return NextResponse.json(
      { error: "Failed to retrieve analysis results" },
      { status: 500 }
    );
  }
}
