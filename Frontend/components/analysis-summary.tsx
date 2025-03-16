"use client"

import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts"

export function AnalysisSummary() {
  // In a real app, this would fetch data from the API
  const data = [
    {
      name: "Linear Feet",
      min: 120,
      avg: 150,
      max: 210,
    },
    {
      name: "Corners",
      min: 6,
      avg: 8,
      max: 12,
    },
    {
      name: "Wall Area",
      min: 960,
      avg: 1200,
      max: 1680,
    },
    {
      name: "Concrete",
      min: 24,
      avg: 30,
      max: 42,
    },
  ]

  return (
    <div className="space-y-4">
      <div className="h-[200px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <XAxis dataKey="name" fontSize={12} />
            <YAxis fontSize={12} />
            <Tooltip />
            <Bar dataKey="min" name="Minimum" fill="#5a7a6a" />
            <Bar dataKey="avg" name="Average" fill="#2f4438" />
            <Bar dataKey="max" name="Maximum" fill="#1a2820" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-md bg-muted/50 p-3">
          <div className="text-sm text-muted-foreground">Total Analyses</div>
          <div className="text-2xl font-bold">24</div>
        </div>
        <div className="rounded-md bg-muted/50 p-3">
          <div className="text-sm text-muted-foreground">Total Projects</div>
          <div className="text-2xl font-bold">5</div>
        </div>
      </div>
    </div>
  )
}

