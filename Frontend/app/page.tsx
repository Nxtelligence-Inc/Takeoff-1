import { readdir, readFile } from "fs/promises"
import path from "path"
import { NotionLayout } from "@/components/notion-layout"
import { Button } from "@/components/ui/button"
import { BarChart3, FileText, Database, Upload, ChevronRight } from "lucide-react"
import Link from "next/link"

// Make this a dynamic page that fetches data at request time
export const dynamic = "force-dynamic"

async function getRecentAnalyses(limit = 3) {
  try {
    const resultsDir = path.join(process.cwd(), "public", "results")
    
    // Check if the directory exists
    try {
      await readdir(resultsDir)
    } catch (error) {
      // Silently return empty array if results directory doesn't exist
      return []
    }
    
    // Get all directories in the results folder
    let analysisDirs
    try {
      analysisDirs = await readdir(resultsDir, { withFileTypes: true })
    } catch (error) {
      // Handle any errors reading the directory
      return []
    }
    
    const analyses = []
    
    // Only process directories
    for (const dir of analysisDirs.filter(dirent => dirent.isDirectory())) {
      try {
        const analysisPath = path.join(resultsDir, dir.name, "analysis_results.json")
        
        // Check if the file exists before trying to read it
        try {
          await readFile(analysisPath, { encoding: 'utf8' })
        } catch (error) {
          // Skip this directory if the file doesn't exist
          continue
        }
        
        const data = await readFile(analysisPath, "utf8")
        const analysis = JSON.parse(data)
        
        analyses.push({
          id: dir.name,
          timestamp: analysis.metadata?.timestamp || new Date().toISOString(),
          drawing_name: analysis.metadata?.drawing_name || "Unnamed Analysis",
          project_id: analysis.metadata?.project_id || "Default Project",
          total_linear_feet: analysis.icf_metrics?.total_linear_feet,
          total_corners: analysis.icf_metrics?.total_corners,
          wall_area_sqft: analysis.icf_metrics?.wall_area_sqft
        })
      } catch (error) {
        // Silently skip any analyses with errors
        continue
      }
    }
    
    // Sort by timestamp (newest first) and limit
    return analyses
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, limit)
  } catch (error) {
    // Return empty array for any errors
    return []
  }
}

async function getMetricsOverview() {
  try {
    const resultsDir = path.join(process.cwd(), "public", "results")
    
    // Check if the directory exists
    try {
      await readdir(resultsDir)
    } catch (error) {
      // Silently return default metrics if results directory doesn't exist
      return {
        total_analyses: 0,
        avg_linear_feet: 0,
        avg_corners: 0
      }
    }
    
    // Get all directories in the results folder
    let analysisDirs
    try {
      analysisDirs = await readdir(resultsDir, { withFileTypes: true })
    } catch (error) {
      // Handle any errors reading the directory
      return {
        total_analyses: 0,
        avg_linear_feet: 0,
        avg_corners: 0
      }
    }
    
    let totalAnalyses = 0
    let totalLinearFeet = 0
    let totalCorners = 0
    
    // Only process directories
    for (const dir of analysisDirs.filter(dirent => dirent.isDirectory())) {
      try {
        const analysisPath = path.join(resultsDir, dir.name, "analysis_results.json")
        
        // Check if the file exists before trying to read it
        try {
          await readFile(analysisPath, { encoding: 'utf8' })
        } catch (error) {
          // Skip this directory if the file doesn't exist
          continue
        }
        
        const data = await readFile(analysisPath, "utf8")
        const analysis = JSON.parse(data)
        
        totalAnalyses++
        
        if (analysis.icf_metrics?.total_linear_feet) {
          totalLinearFeet += parseFloat(analysis.icf_metrics.total_linear_feet)
        }
        
        if (analysis.icf_metrics?.total_corners) {
          totalCorners += parseInt(analysis.icf_metrics.total_corners)
        }
      } catch (error) {
        // Silently skip any analyses with errors
        continue
      }
    }
    
    return {
      total_analyses: totalAnalyses,
      avg_linear_feet: totalAnalyses > 0 ? (totalLinearFeet / totalAnalyses).toFixed(1) : 0,
      avg_corners: totalAnalyses > 0 ? (totalCorners / totalAnalyses).toFixed(1) : 0
    }
  } catch (error) {
    // Return default metrics for any errors
    return {
      total_analyses: 0,
      avg_linear_feet: 0,
      avg_corners: 0
    }
  }
}

export default async function Home() {
  const recentAnalyses = await getRecentAnalyses(3)
  const metrics = await getMetricsOverview()

  return (
    <NotionLayout>
      <div className="max-w-4xl">
        {/* Page header */}
        <div className="mb-8">
          <h1
            className="notion-page-title flex items-center"
            style={{
              fontSize: "30px",
              fontStyle: "normal",
              fontWeight: 605,
              lineHeight: "95%",
              letterSpacing: "-0.04em",
            }}
          >
            <BarChart3 className="notion-page-icon h-8 w-8 mr-3" />
            Foundation Plan Analyzer
          </h1>
          <p className="text-muted-foreground mt-2">Analyze foundation plans for ICF metrics and visualize results</p>
        </div>

        {/* Quick actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Link href="/analyze" className="notion-card p-4 flex flex-col items-center text-center">
            <div className="h-12 w-12 rounded-full bg-secondary flex items-center justify-center mb-3">
              <Upload className="h-6 w-6 text-foreground" />
            </div>
            <h3 className="font-weight-605 mb-1">New Analysis</h3>
            <p className="text-sm text-muted-foreground">Upload and analyze a foundation plan</p>
          </Link>

          <Link href="/analyses" className="notion-card p-4 flex flex-col items-center text-center">
            <div className="h-12 w-12 rounded-full bg-secondary flex items-center justify-center mb-3">
              <FileText className="h-6 w-6 text-foreground" />
            </div>
            <h3 className="font-weight-605 mb-1">View Analyses</h3>
            <p className="text-sm text-muted-foreground">Browse all foundation plan analyses</p>
          </Link>

          <Link href="/database" className="notion-card p-4 flex flex-col items-center text-center">
            <div className="h-12 w-12 rounded-full bg-secondary flex items-center justify-center mb-3">
              <Database className="h-6 w-6 text-foreground" />
            </div>
            <h3 className="font-weight-605 mb-1">Database</h3>
            <p className="text-sm text-muted-foreground">Configure database connections</p>
          </Link>
        </div>

        {/* Recent analyses */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-weight-605">Recent Analyses</h2>
            <Link href="/analyses">
              <Button variant="ghost" size="sm" className="text-muted-foreground">
                View all
                <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </div>

          <div className="space-y-2">
            {recentAnalyses.length > 0 ? (
              recentAnalyses.map((analysis) => (
                <Link
                  href={`/analyses/${analysis.id}`}
                  key={analysis.id}
                  className="notion-block flex items-center p-3 hover:bg-secondary/50"
                >
                  <FileText className="h-5 w-5 text-muted-foreground mr-3" />
                  <div>
                    <h3 className="font-medium">{analysis.drawing_name}</h3>
                    <p className="text-sm text-muted-foreground">
                      {new Date(analysis.timestamp).toLocaleDateString()} • {analysis.total_linear_feet} linear feet • {analysis.total_corners} corners
                    </p>
                  </div>
                </Link>
              ))
            ) : (
              <div className="notion-block p-6 text-center">
                <p className="text-muted-foreground mb-4">No analyses found</p>
                <Link href="/analyze">
                  <Button className="notion-button notion-button-primary">
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Foundation Plan
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Metrics overview */}
        <div>
          <h2 className="text-xl font-weight-605 mb-4">Metrics Overview</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="notion-card p-4">
              <div className="text-sm text-muted-foreground mb-1">Total Analyses</div>
              <div className="text-3xl font-medium">{metrics.total_analyses}</div>
            </div>

            <div className="notion-card p-4">
              <div className="text-sm text-muted-foreground mb-1">Average Linear Feet</div>
              <div className="text-3xl font-medium">{metrics.avg_linear_feet}</div>
            </div>

            <div className="notion-card p-4">
              <div className="text-sm text-muted-foreground mb-1">Average Corners</div>
              <div className="text-3xl font-medium">{metrics.avg_corners}</div>
            </div>
          </div>
        </div>
      </div>
    </NotionLayout>
  )
}
