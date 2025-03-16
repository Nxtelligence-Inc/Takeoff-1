import { readdir, readFile } from "fs/promises"
import path from "path"
import { NotionLayout } from "@/components/notion-layout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { FileText, Search, Upload, BarChart3, Trash2, Eye } from "lucide-react"
import Link from "next/link"

// Make this a dynamic page that fetches data at request time
export const dynamic = "force-dynamic"

async function getAllAnalyses() {
  try {
    const resultsDir = path.join(process.cwd(), "public", "results")
    
    // Check if the directory exists
    try {
      await readdir(resultsDir)
    } catch (error) {
      console.log("Results directory does not exist yet")
      return []
    }
    
    const analysisDirs = await readdir(resultsDir, { withFileTypes: true })
    
    const analyses = []
    
    for (const dir of analysisDirs.filter(dirent => dirent.isDirectory())) {
      try {
        const analysisPath = path.join(resultsDir, dir.name, "analysis_results.json")
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
        console.error(`Error reading analysis ${dir.name}:`, error)
      }
    }
    
    // Sort by timestamp (newest first)
    return analyses.sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )
  } catch (error) {
    console.error("Error listing analyses:", error)
    return []
  }
}

export default async function AnalysesPage() {
  const analyses = await getAllAnalyses()

  return (
    <NotionLayout>
      <div className="max-w-5xl">
        {/* Page header */}
        <div className="flex items-center justify-between mb-8">
          <div>
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
              <FileText className="notion-page-icon h-8 w-8" />
              All Analyses
            </h1>
            <p className="text-muted-foreground mt-2">Browse and filter all foundation plan analyses</p>
          </div>

          <Link href="/analyze">
            <Button className="notion-button notion-button-primary">
              <Upload className="mr-2 h-4 w-4" />
              New Analysis
            </Button>
          </Link>
        </div>

        {/* Filters */}
        <div className="mb-6 flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Filter analyses..." className="pl-8" />
          </div>

          <Select>
            <SelectTrigger className="w-full md:w-[180px]">
              <SelectValue placeholder="Filter by project" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Projects</SelectItem>
              <SelectItem value="default_project">Default Project</SelectItem>
              <SelectItem value="residential_project">Residential Project</SelectItem>
              <SelectItem value="commercial_project">Commercial Project</SelectItem>
            </SelectContent>
          </Select>

          <Select>
            <SelectTrigger className="w-full md:w-[180px]">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">Newest First</SelectItem>
              <SelectItem value="oldest">Oldest First</SelectItem>
              <SelectItem value="linear-feet">Linear Feet (High to Low)</SelectItem>
              <SelectItem value="corners">Corners (High to Low)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Analyses table */}
        <div className="notion-card overflow-hidden">
          <table className="notion-table w-full">
            <thead>
              <tr>
                <th>Drawing Name</th>
                <th>Date</th>
                <th>Project</th>
                <th>Linear Feet</th>
                <th>Corners</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {analyses.length > 0 ? (
                analyses.map((analysis) => (
                  <tr key={analysis.id}>
                    <td>
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{analysis.drawing_name}</span>
                      </div>
                    </td>
                    <td className="text-muted-foreground">{new Date(analysis.timestamp).toLocaleDateString()}</td>
                    <td>{analysis.project_id}</td>
                    <td>{analysis.total_linear_feet} ft</td>
                    <td>{analysis.total_corners}</td>
                    <td>
                      <div className="flex items-center gap-1">
                        <Link href={`/analyses/${analysis.id}`}>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Eye className="h-4 w-4" />
                            <span className="sr-only">View</span>
                          </Button>
                        </Link>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <BarChart3 className="h-4 w-4" />
                          <span className="sr-only">Metrics</span>
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive">
                          <Trash2 className="h-4 w-4" />
                          <span className="sr-only">Delete</span>
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="text-center py-8">
                    <div className="flex flex-col items-center justify-center">
                      <FileText className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
                      <p className="text-muted-foreground mb-4">No analyses found</p>
                      <Link href="/analyze">
                        <Button className="notion-button notion-button-primary">
                          <Upload className="mr-2 h-4 w-4" />
                          Upload Foundation Plan
                        </Button>
                      </Link>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </NotionLayout>
  )
}
