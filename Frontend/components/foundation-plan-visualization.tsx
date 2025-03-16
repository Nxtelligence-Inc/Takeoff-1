"use client"

import { useEffect, useRef, useState } from "react"
import Image from "next/image"

interface FoundationPlanVisualizationProps {
  analysisId: string
}

export function FoundationPlanVisualization({ analysisId }: FoundationPlanVisualizationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [analysisData, setAnalysisData] = useState<any>(null)
  const [lastRefresh, setLastRefresh] = useState<number>(Date.now())

  // Function to refresh the visualization
  const refreshVisualization = () => {
    setLastRefresh(Date.now())
  }

  // Add event listener for wall updates
  useEffect(() => {
    // Create a custom event listener for wall updates
    const handleWallUpdate = () => {
      refreshVisualization()
    }
    
    window.addEventListener('wall-updated', handleWallUpdate)
    
    return () => {
      window.removeEventListener('wall-updated', handleWallUpdate)
    }
  }, [])

  useEffect(() => {
    async function fetchAnalysisData() {
      try {
        setLoading(true)
        setError(null)
        
        // First check if there's a visualization image
        const visualizationUrl = `/results/${analysisId}/perimeter_walls.png`
        
        // Create a new Image to check if the visualization exists
        const img = new window.Image()
        img.src = visualizationUrl
        
        // Wait for the image to load or fail
        const imageExists = await new Promise<boolean>((resolve) => {
          img.onload = () => resolve(true)
          img.onerror = () => resolve(false)
        })
        
        // Always fetch the JSON data for real-time updates
        const response = await fetch(`/results/${analysisId}/analysis_results.json?t=${lastRefresh}`)
        
        if (!response.ok) {
          throw new Error(`Failed to fetch analysis data: ${response.statusText}`)
        }
        
        const data = await response.json()
        setAnalysisData(data)
        
        if (imageExists && !lastRefresh) {
          // Only use the image on first load, after that use canvas for real-time updates
          setImageUrl(visualizationUrl)
          setLoading(false)
          return
        }
        
        // Render the data on the canvas
        renderFoundationPlan(data)
        setLoading(false)
      } catch (err) {
        console.error("Error fetching analysis data:", err)
        setError(err instanceof Error ? err.message : "Failed to load visualization")
        setLoading(false)
      }
    }
    
    fetchAnalysisData()
  }, [analysisId, lastRefresh])
  
  function renderFoundationPlan(data: any) {
    const corners = data.corners || []
    const walls = data.walls || []
    
    const canvas = canvasRef.current
    if (!canvas) return
    
    const ctx = canvas.getContext("2d")
    if (!ctx) return
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    if (corners.length === 0) {
      // Draw a message if no corners
      ctx.fillStyle = "#666"
      ctx.font = "16px sans-serif"
      ctx.textAlign = "center"
      ctx.fillText("No foundation plan data available", canvas.width / 2, canvas.height / 2)
      return
    }
    
    // Set canvas dimensions based on the bounding box of the corners
    const padding = 50
    const minX = Math.min(...corners.map((c: any) => c.x)) - padding
    const minY = Math.min(...corners.map((c: any) => c.y)) - padding
    const maxX = Math.max(...corners.map((c: any) => c.x)) + padding
    const maxY = Math.max(...corners.map((c: any) => c.y)) + padding
    
    // Scale to fit canvas
    const scaleX = canvas.width / (maxX - minX)
    const scaleY = canvas.height / (maxY - minY)
    const scale = Math.min(scaleX, scaleY)
    
    // Draw walls
    ctx.strokeStyle = "#2f4438" // Dark green
    ctx.lineWidth = 2
    
    walls.forEach((wall: any) => {
      const startCorner = corners.find((c: any) => c.id === wall.start_corner_id)
      const endCorner = corners.find((c: any) => c.id === wall.end_corner_id)
      
      if (startCorner && endCorner) {
        ctx.beginPath()
        ctx.moveTo((startCorner.x - minX) * scale, (startCorner.y - minY) * scale)
        ctx.lineTo((endCorner.x - minX) * scale, (endCorner.y - minY) * scale)
        ctx.stroke()
      }
    })
    
    // Draw corners
    ctx.fillStyle = "#5a7a6a" // Lighter green for corners
    corners.forEach((corner: any) => {
      ctx.beginPath()
      ctx.arc((corner.x - minX) * scale, (corner.y - minY) * scale, 5, 0, Math.PI * 2)
      ctx.fill()
    })
    
    // Add corner labels
    ctx.fillStyle = "#1a2820" // Darker green for labels
    ctx.font = "12px sans-serif"
    corners.forEach((corner: any) => {
      ctx.fillText(
        corner.id.toString(), 
        (corner.x - minX) * scale + 8, 
        (corner.y - minY) * scale - 8
      )
    })
    
    // Add wall measurements
    ctx.fillStyle = "#2f4438" // Main green for measurements
    ctx.font = "10px sans-serif"
    walls.forEach((wall: any) => {
      if (wall.length) {
        const startCorner = corners.find((c: any) => c.id === wall.start_corner_id)
        const endCorner = corners.find((c: any) => c.id === wall.end_corner_id)
        
        if (startCorner && endCorner) {
          const midX = ((startCorner.x + endCorner.x) / 2 - minX) * scale
          const midY = ((startCorner.y + endCorner.y) / 2 - minY) * scale
          ctx.fillText(wall.length, midX, midY)
        }
      }
    })
  }
  
  if (loading) {
    return (
      <div className="relative aspect-video w-full overflow-hidden rounded-md border bg-background flex items-center justify-center">
        <div className="text-muted-foreground">Loading visualization...</div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="relative aspect-video w-full overflow-hidden rounded-md border bg-background flex items-center justify-center">
        <div className="text-red-500">{error}</div>
      </div>
    )
  }
  
  if (imageUrl) {
    return (
      <div className="relative aspect-video w-full overflow-hidden rounded-md border bg-background">
        <Image 
          src={imageUrl} 
          alt="Foundation Plan Visualization" 
          fill 
          className="object-contain"
        />
      </div>
    )
  }
  
  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-md border bg-background">
      <canvas ref={canvasRef} width={800} height={600} className="h-full w-full" />
    </div>
  )
}
