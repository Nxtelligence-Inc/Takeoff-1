"use client"

import { useState } from "react"
import { NotionLayout } from "../../components/notion-layout"
import { Button } from "../../components/ui/button"
import { CardContent } from "../../components/ui/card"
import { Input } from "../../components/ui/input"
import { Label } from "../../components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select"
import { Separator } from "../../components/ui/separator"
import { Upload } from "lucide-react"
import { FileUploader } from "../../components/file-uploader"

export default function AnalyzePage() {
  const [drawingName, setDrawingName] = useState("")
  const [projectId, setProjectId] = useState("default_project")
  const [wallThickness, setWallThickness] = useState('8"')
  const [wallHeight, setWallHeight] = useState("8.0")
  const [useLLM, setUseLLM] = useState(true)
  const [visualize, setVisualize] = useState(true)

  return (
    <NotionLayout>
      <div className="max-w-5xl">
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
            <Upload className="notion-page-icon h-8 w-8" />
            Analyze Foundation Plan
          </h1>
          <p className="text-muted-foreground mt-2">Upload a foundation plan to analyze and extract ICF metrics</p>
        </div>

        {/* Main content */}
        <div className="grid gap-6 md:grid-cols-2">
          <div className="notion-card">
            <div className="p-4 border-b border-border/60">
              <h2 className="text-lg font-weight-605">Upload Foundation Plan</h2>
              <p className="text-sm text-muted-foreground">Upload a foundation plan image to analyze</p>
            </div>
            <CardContent className="p-4">
              <FileUploader 
                drawingName={drawingName}
                projectId={projectId}
                wallThickness={wallThickness}
                wallHeight={wallHeight}
                useLLM={useLLM}
                visualize={visualize}
              />
            </CardContent>
          </div>

          <div className="notion-card">
            <div className="p-4 border-b border-border/60">
              <h2 className="text-lg font-weight-605">Analysis Settings</h2>
              <p className="text-sm text-muted-foreground">Configure analysis parameters</p>
            </div>
            <CardContent className="p-4">
              <div className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="drawing-name">Drawing Name</Label>
                  <Input 
                    id="drawing-name" 
                    placeholder="Enter drawing name" 
                    value={drawingName}
                    onChange={(e) => setDrawingName(e.target.value)}
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="project">Project</Label>
                  <Select value={projectId} onValueChange={setProjectId}>
                    <SelectTrigger id="project">
                      <SelectValue placeholder="Select project" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="default_project">Default Project</SelectItem>
                      <SelectItem value="residential_project">Residential Project</SelectItem>
                      <SelectItem value="commercial_project">Commercial Project</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="wall-thickness">Wall Thickness</Label>
                  <Select value={wallThickness} onValueChange={setWallThickness}>
                    <SelectTrigger id="wall-thickness">
                      <SelectValue placeholder="Select wall thickness" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value='6"'>6"</SelectItem>
                      <SelectItem value='8"'>8"</SelectItem>
                      <SelectItem value='10"'>10"</SelectItem>
                      <SelectItem value='12"'>12"</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="wall-height">Wall Height (feet)</Label>
                  <Input 
                    id="wall-height" 
                    type="number" 
                    value={wallHeight}
                    onChange={(e) => setWallHeight(e.target.value)}
                  />
                </div>

                <Separator className="my-2" />

                <div className="grid gap-2">
                  <Label>Analysis Options</Label>
                  <div className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      id="use-llm" 
                      className="h-4 w-4 rounded border-gray-300" 
                      checked={useLLM}
                      onChange={(e) => setUseLLM(e.target.checked)}
                    />
                    <Label htmlFor="use-llm" className="text-sm font-normal">
                      Use LLM for dimension extraction
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input 
                      type="checkbox" 
                      id="visualize" 
                      className="h-4 w-4 rounded border-gray-300" 
                      checked={visualize}
                      onChange={(e) => setVisualize(e.target.checked)}
                    />
                    <Label htmlFor="visualize" className="text-sm font-normal">
                      Generate visualization
                    </Label>
                  </div>
                </div>
              </div>
            </CardContent>
          </div>
        </div>
      </div>
    </NotionLayout>
  )
}
