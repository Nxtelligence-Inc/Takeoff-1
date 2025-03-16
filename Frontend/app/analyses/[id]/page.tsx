import { notFound } from "next/navigation"
import { readFile } from "fs/promises"
import path from "path"
import Image from "next/image"
import { NotionLayout } from "@/components/notion-layout"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Download, Share2, FileText } from "lucide-react"
import { FoundationPlanVisualization } from "@/components/foundation-plan-visualization"
import { ICFMetricsTable } from "@/components/icf-metrics-table"
import { ICFMetricsDisplay } from "@/components/icf-metrics-display"
import { WallsTable } from "@/components/walls-table"
import { ICFMaterialsQuotation } from "@/components/icf-materials-quotation"

// Make this a dynamic page that fetches data at request time
export const dynamic = "force-dynamic"

async function getAnalysisData(id: string) {
  try {
    const resultsPath = path.join(
      process.cwd(),
      "public",
      "results",
      id,
      "analysis_results.json"
    )
    const data = await readFile(resultsPath, "utf8")
    return JSON.parse(data)
  } catch (error) {
    console.error("Error reading analysis data:", error)
    return null
  }
}

export default async function AnalysisDetailPage({ params }: { params: { id: string } }) {
  const analysisData = await getAnalysisData(params.id)
  
  if (!analysisData) {
    notFound()
  }

  const metadata = analysisData.metadata || {}
  const corners = analysisData.corners || []
  const walls = analysisData.walls || []
  const icfMetrics = analysisData.icf_metrics || {}
  
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
              {metadata.drawing_name || "Analysis Details"}
            </h1>
            <p className="text-muted-foreground mt-2">
              Analyzed on {new Date(metadata.timestamp || Date.now()).toLocaleString()}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="text-muted-foreground">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
            <Button variant="outline" size="sm" className="text-muted-foreground">
              <Share2 className="mr-2 h-4 w-4" />
              Share
            </Button>
          </div>
        </div>

        {/* Main content */}
        <div className="grid gap-6 md:grid-cols-3">
          <div className="md:col-span-2">
            <div className="notion-card">
              <div className="p-4 border-b border-border/60">
                <h2 className="text-lg font-weight-605">Foundation Plan</h2>
                <p className="text-sm text-muted-foreground">Visual representation of the analyzed plan</p>
              </div>
              <div className="p-4">
                {metadata.visualization_url ? (
                  <div className="relative aspect-video w-full overflow-hidden rounded-md border bg-background">
                    <Image 
                      src={metadata.visualization_url} 
                      alt="Foundation Plan Visualization" 
                      fill 
                      className="object-contain"
                    />
                  </div>
                ) : (
                  <FoundationPlanVisualization analysisId={params.id} />
                )}
              </div>
            </div>
          </div>

          <div>
            <div className="notion-card">
              <div className="p-4 border-b border-border/60">
                <h2 className="text-lg font-weight-605">ICF Metrics</h2>
                <p className="text-sm text-muted-foreground">Key measurements and calculations</p>
              </div>
              <div className="p-4">
                <ICFMetricsDisplay analysisId={params.id} />
              </div>
            </div>
          </div>
        </div>

        {/* Detailed analysis */}
        <div className="mt-6">
          <div className="notion-card">
            <div className="p-4 border-b border-border/60">
              <h2 className="text-lg font-weight-605">Detailed Analysis</h2>
              <p className="text-sm text-muted-foreground">Comprehensive breakdown of the foundation plan</p>
            </div>
            <div className="p-4">
              <Tabs defaultValue="walls">
                <TabsList className="bg-secondary border border-border/40">
                  <TabsTrigger value="walls" className="text-sm">
                    Walls
                  </TabsTrigger>
                  <TabsTrigger value="corners" className="text-sm">
                    Corners
                  </TabsTrigger>
                  <TabsTrigger value="json" className="text-sm">
                    Raw JSON
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="walls" className="mt-4">
                  <WallsTable analysisId={params.id} />
                </TabsContent>

                <TabsContent value="corners" className="mt-4">
                  <div className="rounded-md border">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b bg-muted/50">
                          <th className="p-2 text-left font-medium">Corner ID</th>
                          <th className="p-2 text-left font-medium">X</th>
                          <th className="p-2 text-left font-medium">Y</th>
                        </tr>
                      </thead>
                      <tbody>
                        {corners.map((corner: any) => (
                          <tr key={corner.id} className="border-b">
                            <td className="p-2">{corner.id}</td>
                            <td className="p-2">{corner.x}</td>
                            <td className="p-2">{corner.y}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </TabsContent>

                <TabsContent value="json" className="mt-4">
                  <pre className="max-h-96 overflow-auto rounded-md bg-muted p-4 text-sm">
                    {JSON.stringify(analysisData, null, 2)}
                  </pre>
                </TabsContent>
              </Tabs>
            </div>
          </div>
        </div>
        
        {/* ICF Materials Quotation */}
        <div className="mt-6">
          <ICFMaterialsQuotation analysisId={params.id} />
        </div>
      </div>
    </NotionLayout>
  )
}
