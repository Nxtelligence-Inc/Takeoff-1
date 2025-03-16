"use client"

import { Button } from "@/components/ui/button"
import { BarChart3, Eye, FileText, Trash2 } from "lucide-react"
import Link from "next/link"

export function AnalysesTable() {
  // In a real app, this would fetch data from the API
  const analyses = [
    {
      id: "fcaf4833-a0a1-4292-baef-6b953ecc75b5",
      timestamp: "2025-03-15T10:28:28",
      drawing_name: "Screenshot2",
      project_id: "test_project",
      total_linear_feet: 150.2,
      total_corners: 8,
      wall_area_sqft: 1202.0,
    },
    {
      id: "1b8dfc78-197a-4e28-8285-ed91d196cc93",
      timestamp: "2025-03-15T10:29:51",
      drawing_name: "perimeter_walls",
      project_id: "example_project",
      total_linear_feet: 145.8,
      total_corners: 7,
      wall_area_sqft: 1166.4,
    },
    {
      id: "3a7e9c12-b4d8-4f1e-9c6a-8d2f5e7b3c9a",
      timestamp: "2025-03-14T14:22:15",
      drawing_name: "foundation_plan_1",
      project_id: "residential_project",
      total_linear_feet: 162.5,
      total_corners: 10,
      wall_area_sqft: 1300.0,
    },
    {
      id: "5c9b8a76-e4d2-4f1e-9c6a-8d2f5e7b3c9a",
      timestamp: "2025-03-13T09:15:30",
      drawing_name: "commercial_foundation",
      project_id: "commercial_project",
      total_linear_feet: 210.3,
      total_corners: 12,
      wall_area_sqft: 1682.4,
    },
  ]

  return (
    <div className="rounded-md border">
      <table className="w-full">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="p-2 text-left font-medium">Drawing Name</th>
            <th className="p-2 text-left font-medium">Date</th>
            <th className="p-2 text-left font-medium">Project</th>
            <th className="p-2 text-left font-medium">Linear Feet</th>
            <th className="p-2 text-left font-medium">Corners</th>
            <th className="p-2 text-left font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {analyses.map((analysis) => (
            <tr key={analysis.id} className="border-b">
              <td className="p-2 font-weight-605">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  {analysis.drawing_name}
                </div>
              </td>
              <td className="p-2 text-muted-foreground">{new Date(analysis.timestamp).toLocaleDateString()}</td>
              <td className="p-2">{analysis.project_id}</td>
              <td className="p-2">{analysis.total_linear_feet} ft</td>
              <td className="p-2">{analysis.total_corners}</td>
              <td className="p-2">
                <div className="flex items-center gap-1">
                  <Link href={`/analyses/${analysis.id}`}>
                    <Button variant="ghost" size="icon" className="h-8 w-8" style={{ color: "#2f4438" }}>
                      <Eye className="h-4 w-4" />
                      <span className="sr-only">View</span>
                    </Button>
                  </Link>
                  <Link href={`/analyses/${analysis.id}/metrics`}>
                    <Button variant="ghost" size="icon" className="h-8 w-8" style={{ color: "#2f4438" }}>
                      <BarChart3 className="h-4 w-4" />
                      <span className="sr-only">Metrics</span>
                    </Button>
                  </Link>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive">
                    <Trash2 className="h-4 w-4" />
                    <span className="sr-only">Delete</span>
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

