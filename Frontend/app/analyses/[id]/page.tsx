"use client"
import { notFound } from "next/navigation"
import { useState, useEffect } from "react"
import Image from "next/image"
import { NotionLayout } from "@/components/notion-layout"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { FileText } from "lucide-react"
import { AnalysisExportActions } from "@/components/analysis-export-actions"
import { FoundationPlanVisualization } from "@/components/foundation-plan-visualization"
import { ICFMetricsTable } from "@/components/icf-metrics-table"
import { ICFMetricsDisplay } from "@/components/icf-metrics-display"
import { WallsTable } from "@/components/walls-table"
import { ICFMaterialsQuotation, ICFMaterialsCalculation } from "@/components/icf-materials-quotation"

// Make this a dynamic page that fetches data at request time
export const dynamic = "force-dynamic"

async function getAnalysisData(id: string) {
  try {
    const response = await fetch(`/results/${id}/analysis_results.json`)
    if (!response.ok) {
      throw new Error(`Failed to fetch analysis data: ${response.statusText}`)
    }
    const data = await response.json()
    return data
  } catch (error) {
    console.error("Error fetching analysis data:", error)
    return null
  }
}

export default function AnalysisDetailPage({ params }: { params: { id: string } }) {
  const [materials, setMaterials] = useState<ICFMaterialsCalculation | null>(null)
  const [analysisData, setAnalysisData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        const data = await getAnalysisData(params.id)
        if (!data) {
          notFound()
        }
        setAnalysisData(data)
        setLoading(false)
      } catch (err) {
        console.error("Error loading analysis data:", err)
        setError(err instanceof Error ? err.message : "Failed to load analysis")
        setLoading(false)
      }
    }
    loadData()
  }, [params.id])

  if (loading) {
    return <div className="p-4 text-center">Loading analysis data...</div>
  }

  if (error || !analysisData) {
    return <div className="p-4 text-center text-red-500">{error || "Analysis not found"}</div>
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

          {materials && (
            <AnalysisExportActions
              analysisId={params.id}
              drawingName={metadata.drawing_name || "Unnamed Analysis"}
              projectId={metadata.project_id || "Default Project"}
              timestamp={metadata.timestamp || new Date().toISOString()}
              materials={materials}
            />
          )}
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
          <ICFMaterialsQuotation 
            analysisId={params.id} 
            onCalculation={setMaterials}
          />
        </div>
      </div>
    </NotionLayout>
  )
}
