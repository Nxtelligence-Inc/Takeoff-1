"use client"

import { BarChart3, FileText } from "lucide-react"
import Link from "next/link"

export function RecentAnalyses() {
  // In a real app, this would fetch data from the API
  const recentAnalyses = [
    {
      id: "fcaf4833-a0a1-4292-baef-6b953ecc75b5",
      timestamp: "2025-03-15T10:28:28",
      drawing_name: "Screenshot2",
      project_id: "test_project",
      total_linear_feet: 150.2,
    },
    {
      id: "1b8dfc78-197a-4e28-8285-ed91d196cc93",
      timestamp: "2025-03-15T10:29:51",
      drawing_name: "perimeter_walls",
      project_id: "example_project",
      total_linear_feet: 145.8,
    },
    {
      id: "3a7e9c12-b4d8-4f1e-9c6a-8d2f5e7b3c9a",
      timestamp: "2025-03-14T14:22:15",
      drawing_name: "foundation_plan_1",
      project_id: "residential_project",
      total_linear_feet: 162.5,
    },
  ]

  return (
    <div className="space-y-4">
      {recentAnalyses.map((analysis) => (
        <Link key={analysis.id} href={`/analyses/${analysis.id}`}>
          <div className="flex items-center justify-between rounded-md border p-3 transition-colors hover:bg-muted/50">
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-muted-foreground" />
              <div>
                <div className="font-weight-605">{analysis.drawing_name}</div>
                <div className="text-xs text-muted-foreground">
                  {new Date(analysis.timestamp).toLocaleDateString()} • {analysis.project_id}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1 text-sm">
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
              <span>{analysis.total_linear_feet} ft</span>
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
}

