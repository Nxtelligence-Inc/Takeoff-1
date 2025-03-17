"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Edit2, Save, X } from "lucide-react"

interface Wall {
  id: number
  start_corner_id: number
  end_corner_id: number
  start_x: number
  start_y: number
  end_x: number
  end_y: number
  length_pixels: number
  length: string
}

interface WallsTableProps {
  analysisId: string
}

export function WallsTable({ analysisId }: WallsTableProps) {
  const [walls, setWalls] = useState<Wall[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingWall, setEditingWall] = useState<number | null>(null)
  const [editFeet, setEditFeet] = useState<number>(0)
  const [editInches, setEditInches] = useState<number>(0)
  const [isSaving, setIsSaving] = useState(false)

  // Parse feet and inches from a string like "34'-0\""
  const parseFeetInches = (lengthStr: string): { feet: number, inches: number } => {
    try {
      // Remove any escape characters and normalize quotes
      const cleaned = lengthStr.replace(/\\"/g, '"').replace(/"/g, '"')
      
      // Split on the feet symbol
      const parts = cleaned.split("'")
      const feet = parseInt(parts[0], 10)
      
      // Parse inches (remove the inch symbol and any negative signs)
      let inches = 0
      if (parts.length > 1) {
        // Remove inch symbol, negative signs, and trim whitespace
        const inchPart = parts[1].replace(/"/g, '').replace(/-/g, '').trim()
        if (inchPart && inchPart !== '0') {
          inches = parseInt(inchPart, 10)
        }
      }
      
      return { feet, inches }
    } catch (error) {
      // Silently handle parsing errors
      return { feet: 0, inches: 0 }
    }
  }

  // Format feet and inches back to a string
  const formatFeetInches = (feet: number, inches: number): string => {
    return `${feet}'-${inches}"`
  }

  // Fetch walls data
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        setError(null)
        
        const response = await fetch(`/results/${analysisId}/analysis_results.json`)
        
        if (!response.ok) {
          throw new Error(`Failed to fetch analysis data: ${response.statusText}`)
        }
        
        const data = await response.json()
        
        if (data.walls && Array.isArray(data.walls)) {
          setWalls(data.walls)
        } else {
          setWalls([])
        }
        
        setLoading(false)
      } catch (err) {
        // Set error state instead of logging to console
        setError(err instanceof Error ? err.message : "Failed to load walls data")
        setLoading(false)
      }
    }
    
    fetchData()
  }, [analysisId])

  // Start editing a wall
  const handleEditClick = (wall: Wall) => {
    const { feet, inches } = parseFeetInches(wall.length)
    setEditFeet(feet)
    setEditInches(inches)
    setEditingWall(wall.id)
  }

  // Cancel editing
  const handleCancelEdit = () => {
    setEditingWall(null)
  }

  // Save edited wall length
  const handleSaveEdit = async (wallId: number) => {
    try {
      setIsSaving(true)
      
      // Find the wall being edited
      const wallIndex = walls.findIndex(w => w.id === wallId)
      if (wallIndex === -1) return
      
      // Format the new length
      const newLength = formatFeetInches(editFeet, editInches)
      
      // Create updated walls array
      const updatedWalls = [...walls]
      updatedWalls[wallIndex] = {
        ...updatedWalls[wallIndex],
        length: newLength
      }
      
      // Update state
      setWalls(updatedWalls)
      
      // Save to server
      const response = await fetch(`/api/analyses/${analysisId}/update-wall`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          wallId,
          newLength
        }),
      })
      
      if (!response.ok) {
        throw new Error(`Failed to update wall: ${response.statusText}`)
      }
      
      // Get the updated metrics from the response
      const result = await response.json()
      
      // Dispatch a custom event to notify other components of the update
      const updateEvent = new CustomEvent('wall-updated', { 
        detail: { 
          wallId, 
          newLength,
          updatedMetrics: result.updatedMetrics
        } 
      })
      window.dispatchEvent(updateEvent)
      
      // Reset editing state
      setEditingWall(null)
      setIsSaving(false)
    } catch (err) {
      // Show alert instead of logging to console
      alert("Failed to save changes. Please try again.")
      setIsSaving(false)
    }
  }

  if (loading) {
    return <div className="p-4 text-center">Loading walls data...</div>
  }

  if (error) {
    return <div className="p-4 text-center text-red-500">{error}</div>
  }

  if (walls.length === 0) {
    return <div className="p-4 text-center">No walls data available</div>
  }

  return (
    <div className="rounded-md border">
      <table className="w-full">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="p-2 text-left font-medium">Wall ID</th>
            <th className="p-2 text-left font-medium">Start Corner</th>
            <th className="p-2 text-left font-medium">End Corner</th>
            <th className="p-2 text-left font-medium">Length</th>
            <th className="p-2 text-left font-medium">Start (x,y)</th>
            <th className="p-2 text-left font-medium">End (x,y)</th>
            <th className="p-2 text-left font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {walls.map((wall) => (
            <tr key={wall.id} className="border-b">
              <td className="p-2">{wall.id}</td>
              <td className="p-2">{wall.start_corner_id}</td>
              <td className="p-2">{wall.end_corner_id}</td>
              <td className="p-2 font-weight-605">
                {editingWall === wall.id ? (
                  <div className="flex items-center space-x-1">
                    <Input
                      type="number"
                      value={editFeet}
                      onChange={(e) => setEditFeet(parseInt(e.target.value, 10) || 0)}
                      className="w-16 h-8"
                      min={0}
                    />
                    <span>ft</span>
                    <Input
                      type="number"
                      value={editInches}
                      onChange={(e) => setEditInches(parseInt(e.target.value, 10) || 0)}
                      className="w-16 h-8"
                      min={0}
                      max={11}
                    />
                    <span>in</span>
                  </div>
                ) : (
                  <span className="cursor-pointer hover:text-blue-500" onClick={() => handleEditClick(wall)}>
                    {wall.length}
                  </span>
                )}
              </td>
              <td className="p-2">
                ({wall.start_x}, {wall.start_y})
              </td>
              <td className="p-2">
                ({wall.end_x}, {wall.end_y})
              </td>
              <td className="p-2">
                {editingWall === wall.id ? (
                  <div className="flex items-center space-x-1">
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-8 w-8 text-green-500"
                      onClick={() => handleSaveEdit(wall.id)}
                      disabled={isSaving}
                    >
                      <Save className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-8 w-8 text-red-500"
                      onClick={handleCancelEdit}
                      disabled={isSaving}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ) : (
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8"
                    onClick={() => handleEditClick(wall)}
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
