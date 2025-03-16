import Link from "next/link"
import { BarChart3, FileText, Home } from "lucide-react"

export default function StyledDemo() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="custom-header">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-6 w-6" />
            <h1 className="text-xl font-bold">Foundation Plan Analyzer</h1>
          </div>
          <nav className="flex items-center gap-4">
            <Link href="#" className="nav-item active">
              <Home className="h-5 w-5" />
            </Link>
            <Link href="#" className="nav-item">
              <FileText className="h-5 w-5" />
            </Link>
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
        <div className="mt-8 p-4 border rounded-lg">
          <h2 className="text-xl font-bold mb-4">Foundation Plan Visualization</h2>
          <div className="visualization-container">
            <div className="foundation-plan" style={{ width: "500px", height: "300px" }}>
              {/* Sample corner points */}
              <div className="corner-point" style={{ left: "100px", top: "100px" }}></div>
              <div className="corner-point" style={{ left: "400px", top: "100px" }}></div>
              <div className="corner-point" style={{ left: "400px", top: "200px" }}></div>
              <div className="corner-point" style={{ left: "100px", top: "200px" }}></div>

              {/* Sample wall lines */}
              <div
                className="wall-line"
                style={{
                  left: "100px",
                  top: "100px",
                  width: "300px",
                  transform: "rotate(0deg)",
                }}
              ></div>
              <div
                className="wall-line"
                style={{
                  left: "400px",
                  top: "100px",
                  width: "100px",
                  transform: "rotate(90deg)",
                }}
              ></div>
              <div
                className="wall-line"
                style={{
                  left: "400px",
                  top: "200px",
                  width: "300px",
                  transform: "rotate(180deg)",
                }}
              ></div>
              <div
                className="wall-line"
                style={{
                  left: "100px",
                  top: "200px",
                  width: "100px",
                  transform: "rotate(270deg)",
                }}
              ></div>

              {/* Sample dimension labels */}
              <div className="dimension-label" style={{ left: "250px", top: "80px" }}>
                30'-0"
              </div>
              <div className="dimension-label" style={{ left: "420px", top: "150px" }}>
                10'-0"
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

