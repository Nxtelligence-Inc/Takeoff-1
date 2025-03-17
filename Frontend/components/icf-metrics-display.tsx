"use client"

import { useState, useEffect } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Edit2, Save, X } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface ICFMetricsDisplayProps {
  analysisId: string
}

export function ICFMetricsDisplay({ analysisId }: ICFMetricsDisplayProps) {
  const [metrics, setMetrics] = useState<any>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<number>(Date.now())
  
  // Editing states
  const [editingWallThickness, setEditingWallThickness] = useState(false)
  const [editingWallHeight, setEditingWallHeight] = useState(false)
  const [wallThicknessInches, setWallThicknessInches] = useState<number>(6)
  const [wallHeightFeet, setWallHeightFeet] = useState<number>(8)

  // Function to refresh the metrics
  const refreshMetrics = () => {
    setLastRefresh(Date.now())
  }

  // Add event listener for wall updates
  useEffect(() => {
    // Create a custom event listener for wall updates
    const handleWallUpdate = (event: any) => {
      // If the event contains updated metrics, use them directly
      if (event.detail?.updatedMetrics) {
        setMetrics((prevMetrics: any) => ({
          ...prevMetrics,
          ...event.detail.updatedMetrics
        }))
      } else {
        // Otherwise, trigger a refresh
        refreshMetrics()
      }
    }
    
    window.addEventListener('wall-updated', handleWallUpdate)
    
    return () => {
      window.removeEventListener('wall-updated', handleWallUpdate)
    }
  }, [])
  
  // Parse wall thickness when metrics change
  useEffect(() => {
    if (metrics.wall_thickness) {
      // Parse wall thickness (convert from string like "8\"" to number)
      try {
        const thicknessMatch = metrics.wall_thickness.match(/(\d+)/)
        if (thicknessMatch && thicknessMatch[1]) {
          setWallThicknessInches(parseInt(thicknessMatch[1], 10))
        }
      } catch (e) {
        // Silently handle parsing errors
      }
    }
    
    if (metrics.wall_height) {
      setWallHeightFeet(parseFloat(metrics.wall_height))
    }
  }, [metrics.wall_thickness, metrics.wall_height])

  // Fetch metrics data
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        setError(null)
        
        const response = await fetch(`/results/${analysisId}/analysis_results.json?t=${lastRefresh}`)
        
        if (!response.ok) {
          throw new Error(`Failed to fetch analysis data: ${response.statusText}`)
        }
        
        const data = await response.json()
        
        setMetrics({
          ...data.icf_metrics,
          wall_thickness: data.metadata?.wall_thickness || data.wall_thickness,
          wall_height: data.metadata?.wall_height || data.icf_metrics?.assumptions?.wall_height_feet
        })
        
        setLoading(false)
      } catch (err) {
        // Set error state instead of logging to console
        setError(err instanceof Error ? err.message : "Failed to load metrics data")
        setLoading(false)
      }
    }
    
    fetchData()
  }, [analysisId, lastRefresh])
  
  // Handle saving wall thickness
  const handleSaveWallThickness = () => {
    // Format wall thickness
    const formattedThickness = `${wallThicknessInches}"`
    
    // Update metrics
    setMetrics((prevMetrics: any) => ({
      ...prevMetrics,
      wall_thickness: formattedThickness
    }))
    
    // Dispatch custom event for ICF Materials Quotation
    const updateEvent = new CustomEvent('icf-dimension-updated', { 
      detail: { 
        type: 'wall_thickness',
        value: wallThicknessInches
      } 
    })
    window.dispatchEvent(updateEvent)
    
    // Exit edit mode
    setEditingWallThickness(false)
  }
  
  // Handle saving wall height
  const handleSaveWallHeight = () => {
    // Format wall height
    const formattedHeight = `${wallHeightFeet}`
    
    // Update metrics
    setMetrics((prevMetrics: any) => ({
      ...prevMetrics,
      wall_height: formattedHeight
    }))
    
    // Dispatch custom event for ICF Materials Quotation
    const updateEvent = new CustomEvent('icf-dimension-updated', { 
      detail: { 
        type: 'wall_height',
        value: wallHeightFeet
      } 
    })
    window.dispatchEvent(updateEvent)
    
    // Exit edit mode
    setEditingWallHeight(false)
  }

  if (loading) {
    return <div className="p-4 text-center">Loading metrics data...</div>
  }

  if (error) {
    return <div className="p-4 text-center text-red-500">{error}</div>
  }

  return (
    <div className="space-y-4">
      <div>
        <div className="text-sm text-muted-foreground">Total Linear Feet</div>
        <div className="text-xl font-medium">{metrics.total_linear_feet}</div>
      </div>
      <div>
        <div className="text-sm text-muted-foreground">Total Corners</div>
        <div className="text-xl font-medium">{metrics.total_corners}</div>
      </div>
      <div>
        <div className="text-sm text-muted-foreground">Wall Area</div>
        <div className="text-xl font-medium">{metrics.wall_area_sqft} sq ft</div>
      </div>
      <div>
        <div className="text-sm text-muted-foreground">Concrete Volume</div>
        <div className="text-xl font-medium">{metrics.concrete_volume_cuyd} cu yd</div>
      </div>
      <div>
        <div className="text-sm text-muted-foreground">Wall Thickness</div>
        {editingWallThickness ? (
          <div className="flex items-center space-x-2">
            <Select
              value={wallThicknessInches.toString()}
              onValueChange={(value) => setWallThicknessInches(parseInt(value, 10))}
            >
              <SelectTrigger className="w-24 h-8">
                <SelectValue placeholder="Select thickness" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="6">6"</SelectItem>
                <SelectItem value="8">8"</SelectItem>
                <SelectItem value="10">10"</SelectItem>
                <SelectItem value="12">12"</SelectItem>
              </SelectContent>
            </Select>
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-8 w-8 text-green-500"
              onClick={handleSaveWallThickness}
            >
              <Save className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-8 w-8 text-red-500"
              onClick={() => setEditingWallThickness(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <div className="flex items-center space-x-2">
            <div className="text-xl font-medium">{metrics.wall_thickness}</div>
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-6 w-6"
              onClick={() => setEditingWallThickness(true)}
            >
              <Edit2 className="h-3 w-3" />
            </Button>
          </div>
        )}
      </div>
      <div>
        <div className="text-sm text-muted-foreground">Wall Height</div>
        {editingWallHeight ? (
          <div className="flex items-center space-x-2">
            <Input
              type="number"
              value={wallHeightFeet}
              onChange={(e) => setWallHeightFeet(parseFloat(e.target.value) || 8)}
              className="w-24 h-8"
              step="0.5"
              min="7"
              max="12"
            />
            <span className="text-sm">ft</span>
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-8 w-8 text-green-500"
              onClick={handleSaveWallHeight}
            >
              <Save className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-8 w-8 text-red-500"
              onClick={() => setEditingWallHeight(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <div className="flex items-center space-x-2">
            <div className="text-xl font-medium">{metrics.wall_height} ft</div>
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-6 w-6"
              onClick={() => setEditingWallHeight(true)}
            >
              <Edit2 className="h-3 w-3" />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
