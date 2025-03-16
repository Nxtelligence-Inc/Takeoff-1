"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { BarChart3, FileText, Home } from "lucide-react"

export default function CSSEditor() {
  const [activeTab, setActiveTab] = useState("dashboard")

  return (
    <div className="min-h-screen bg-background">
      {/* Custom CSS */}
      <style jsx global>{`
        /* Edit these styles to see changes in real-time */
        
        /* Header styling */
        .custom-header {
          background-color: #1e293b;
          color: white;
          border-bottom: 1px solid #334155;
          padding: 1rem;
        }
        
        /* Navigation styling */
        .nav-item {
          padding: 0.5rem 1rem;
          border-radius: 0.375rem;
          transition: all 0.2s;
        }
        
        .nav-item:hover {
          background-color: rgba(255, 255, 255, 0.1);
        }
        
        .nav-item.active {
          background-color: #3b82f6;
          color: white;
        }
        
        /* Card styling */
        .custom-card {
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          overflow: hidden;
          transition: all 0.3s;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        .custom-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        
        .card-header {
          background-color: #f8fafc;
          border-bottom: 1px solid #e2e8f0;
        }
        
        /* Metrics styling */
        .metric-value {
          font-size: 2rem;
          font-weight: bold;
          color: #3b82f6;
        }
        
        .metric-label {
          color: #64748b;
          font-size: 0.875rem;
        }
        
        /* Visualization area */
        .visualization-container {
          background-color: #f1f5f9;
          border: 2px dashed #cbd5e1;
          border-radius: 0.5rem;
          padding: 1rem;
          min-height: 200px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
      `}</style>

      {/* Header */}
      <header className="custom-header">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-6 w-6" />
            <h1 className="text-xl font-bold">Foundation Plan Analyzer</h1>
          </div>
          <nav className="flex items-center gap-4">
            <button
              className={`nav-item ${activeTab === "dashboard" ? "active" : ""}`}
              onClick={() => setActiveTab("dashboard")}
            >
              <Home className="h-5 w-5" />
            </button>
            <button
              className={`nav-item ${activeTab === "analyses" ? "active" : ""}`}
              onClick={() => setActiveTab("analyses")}
            >
              <FileText className="h-5 w-5" />
            </button>
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto py-8">
        <div className="grid gap-6 md:grid-cols-3">
          {/* Metrics cards */}
          <div className="custom-card">
            <div className="card-header p-4">
              <h2 className="text-lg font-medium">Total Linear Feet</h2>
            </div>
            <div className="p-4">
              <div className="metric-value">150.2</div>
              <div className="metric-label">Foundation perimeter</div>
            </div>
          </div>

          <div className="custom-card">
            <div className="card-header p-4">
              <h2 className="text-lg font-medium">Total Corners</h2>
            </div>
            <div className="p-4">
              <div className="metric-value">8</div>
              <div className="metric-label">Corner count</div>
            </div>
          </div>

          <div className="custom-card">
            <div className="card-header p-4">
              <h2 className="text-lg font-medium">Wall Area</h2>
            </div>
            <div className="p-4">
              <div className="metric-value">1,202</div>
              <div className="metric-label">Square feet</div>
            </div>
          </div>
        </div>

        {/* Visualization area */}
        <div className="mt-8">
          <Card>
            <CardHeader>
              <CardTitle>Foundation Plan Visualization</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="visualization-container">
                <p className="text-gray-500">Edit the CSS to style this visualization area</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action buttons */}
        <div className="mt-8 flex justify-end gap-4">
          <Button variant="outline">Reset</Button>
          <Button>Save Changes</Button>
        </div>
      </main>
    </div>
  )
}

