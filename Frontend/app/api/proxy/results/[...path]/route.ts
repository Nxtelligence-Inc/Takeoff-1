import { NextRequest, NextResponse } from "next/server";
import { readFile } from "fs/promises";
import path from "path";

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  try {
    // Join the path segments to form the file path
    const filePath = params.path.join("/");
    
    // Check if we're running in a containerized environment
    const IS_CONTAINERIZED = process.env.CONTAINERIZED === "true";
    
    // Define paths for both containerized and local environments
    let fullPath;
    let possiblePaths = [];
    
    if (IS_CONTAINERIZED) {
      // In containerized environment, try multiple possible locations
      possiblePaths = [
        path.join("/app/public/results", filePath),
        path.join("/app/results", filePath),
        path.join(process.cwd(), "public", "results", filePath)
      ];
    } else {
      // In local environment, try multiple possible locations
      possiblePaths = [
        path.join(process.cwd(), "public", "results", filePath),
        path.join(process.cwd(), "..", "public", "results", filePath),
        path.join(process.cwd(), "Frontend", "public", "results", filePath)
      ];
    }
    
    // Try each path until we find the file
    let fileFound = false;
    let fileData: Buffer | null = null;
    
    for (const testPath of possiblePaths) {
      try {
        fileData = await readFile(testPath);
        fullPath = testPath;
        fileFound = true;
        console.log(`Found file at: ${fullPath}`);
        break;
      } catch (error) {
        console.log(`File not found at: ${testPath}`);
      }
    }
    
    if (!fileFound || !fileData) {
      console.error(`Could not find file: ${filePath} in any location`);
      return NextResponse.json(
        { error: "File not found" },
        { status: 404 }
      );
    }
    
    // Determine content type based on file extension
    const ext = path.extname(filePath).toLowerCase();
    let contentType = "application/octet-stream"; // Default content type
    
    switch (ext) {
      case ".json":
        contentType = "application/json";
        break;
      case ".png":
        contentType = "image/png";
        break;
      case ".jpg":
      case ".jpeg":
        contentType = "image/jpeg";
        break;
      case ".svg":
        contentType = "image/svg+xml";
        break;
      case ".pdf":
        contentType = "application/pdf";
        break;
      case ".txt":
        contentType = "text/plain";
        break;
    }
    
    // Return the file with appropriate content type
    return new NextResponse(fileData, {
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
      }
    });
    
  } catch (error) {
    console.error("Error in proxy route:", error);
    return NextResponse.json(
      { error: "Failed to retrieve file" },
      { status: 500 }
    );
  }
}
