"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ICFCalculationSettings } from "./icf-calculation-settings"
import { ICFMaterialsSummary } from "./icf-materials-summary"

interface ICFMaterialsQuotationProps {
  analysisId: string;
  onCalculation?: (materials: ICFMaterialsCalculation | null) => void;
}

export interface ICFSettings {
  // Panel specifications
  panelWidth: number; // inches
  panelHeight: number; // inches
  formThickness: number; // inches
  concreteCore: number; // inches
  
  // Rebar requirements
  verticalRebarType: string; // e.g., "#4" or "#5"
  verticalRebarSpacing: number; // inches
  horizontalRebarType: string; // e.g., "#4"
  horizontalRebarCourses: number;
  
  // Concrete specifications
  concretePsi: number;
  concreteSlump: number; // inches
  concreteWasteFactor: number; // percentage
  
  // Accessories
  formAlignmentSpacing: number; // feet
  bracingSpacing: number; // feet
  windowDoorBucks: boolean;
  fasteningStrips: boolean;
}

export interface ICFMaterialsCalculation {
  // Panel requirements
  standardPanels: {
    count: number;
    areaSqft: number;
  };
  cornerPanels: {
    count: number;
  };
  
  // Rebar requirements
  verticalRebar: {
    type: string;
    lengthFeet: number;
    count: number;
  };
  horizontalRebar: {
    type: string;
    lengthFeet: number;
    count: number;
  };
  
  // Concrete requirements
  concrete: {
    strengthPsi: number;
    slumpInches: number;
    volumeCuYd: number;
    volumeWithWaste: number;
  };
  
  // Accessories
  formAlignmentSystems: {
    count: number;
  };
  bracing: {
    count: number;
  };
  windowDoorBucks: {
    linearFeet: number;
  };
  fasteningStrips: {
    count: number;
  };
  
  // Labor estimates
  labor: {
    crewDays: number;
    pourTimeHours: number;
  };
}

export function ICFMaterialsQuotation({ analysisId, onCalculation }: ICFMaterialsQuotationProps) {
  const [analysisData, setAnalysisData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [settings, setSettings] = useState<ICFSettings>({
    // Default values based on provided specifications
    panelWidth: 16, // inches
    panelHeight: 48, // inches
    formThickness: 5, // inches (2.5" on each side)
    concreteCore: 6, // inches (most common for residential)
    
    verticalRebarType: "#4", // 1/2" diameter
    verticalRebarSpacing: 24, // inches
    horizontalRebarType: "#4", // 1/2" diameter
    horizontalRebarCourses: 3,
    
    concretePsi: 3500, // PSI
    concreteSlump: 5.5, // inches
    concreteWasteFactor: 10, // percentage
    
    formAlignmentSpacing: 6, // feet
    bracingSpacing: 5, // feet
    windowDoorBucks: true,
    fasteningStrips: true
  })
  const [materials, setMaterials] = useState<ICFMaterialsCalculation | null>(null)

  // Fetch analysis data
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
        setAnalysisData(data)
        
        setLoading(false)
      } catch (err) {
        console.error("Error fetching analysis data:", err)
        setError(err instanceof Error ? err.message : "Failed to load analysis data")
        setLoading(false)
      }
    }
    
    fetchData()
  }, [analysisId])

  // Initialize settings based on wall height and thickness
  useEffect(() => {
    if (!analysisData) return
    
    // Extract wall height and thickness from analysis data
    const icfMetrics = analysisData.icf_metrics || {}
    const metadata = analysisData.metadata || {}
    const wallHeightFeet = parseFloat(icfMetrics.assumptions?.wall_height_feet || metadata.wall_height || "8.0")
    const wallThicknessStr = metadata.wall_thickness || analysisData.wall_thickness || "8\""
    
    // Parse wall thickness (convert from string like "8\"" to number)
    let wallThicknessInches = 6 // Default
    try {
      // Remove quotes and other characters, just get the number
      const thicknessMatch = wallThicknessStr.match(/(\d+)/)
      if (thicknessMatch && thicknessMatch[1]) {
        wallThicknessInches = parseInt(thicknessMatch[1], 10)
      }
    } catch (e) {
      console.error("Error parsing wall thickness:", e)
    }
    
    // Adjust settings based on wall height and thickness
    const newSettings = { ...settings }
    
    // Adjust concrete core based on wall thickness
    newSettings.concreteCore = wallThicknessInches
    
    // Adjust vertical rebar type and spacing based on wall height and thickness
    if (wallHeightFeet > 9) {
      // For taller walls, use stronger rebar and closer spacing
      newSettings.verticalRebarType = "#5"
      newSettings.verticalRebarSpacing = 16
    } else if (wallThicknessInches >= 8) {
      // For thicker walls, use stronger rebar
      newSettings.verticalRebarType = "#5"
      newSettings.verticalRebarSpacing = 24
    }
    
    // Adjust horizontal rebar courses based on wall height
    newSettings.horizontalRebarCourses = Math.max(3, Math.ceil(wallHeightFeet / 3))
    
    // Adjust bracing spacing based on wall height
    if (wallHeightFeet > 9) {
      newSettings.bracingSpacing = 4 // Closer bracing for taller walls
    }
    
    // Update settings
    setSettings(newSettings)
  }, [analysisData])
  
  // Listen for dimension updates from ICFMetricsDisplay
  useEffect(() => {
    const handleDimensionUpdate = (event: any) => {
      const { type, value } = event.detail
      
      // Create a copy of current settings
      const newSettings = { ...settings }
      
      if (type === 'wall_thickness') {
        // Update concrete core width
        newSettings.concreteCore = value
        
        // Adjust vertical rebar type based on thickness
        if (value >= 8) {
          newSettings.verticalRebarType = "#5"
        } else {
          newSettings.verticalRebarType = "#4"
        }
      } else if (type === 'wall_height') {
        // Adjust vertical rebar spacing based on height
        if (value > 9) {
          newSettings.verticalRebarType = "#5"
          newSettings.verticalRebarSpacing = 16
          newSettings.bracingSpacing = 4
        } else {
          // Only reset spacing if we're not already using #5 rebar for thickness
          if (newSettings.concreteCore < 8) {
            newSettings.verticalRebarType = "#4"
            newSettings.verticalRebarSpacing = 24
          }
          newSettings.bracingSpacing = 5
        }
        
        // Adjust horizontal rebar courses based on height
        newSettings.horizontalRebarCourses = Math.max(3, Math.ceil(value / 3))
      }
      
      // Update settings
      setSettings(newSettings)
    }
    
    window.addEventListener('icf-dimension-updated', handleDimensionUpdate)
    
    return () => {
      window.removeEventListener('icf-dimension-updated', handleDimensionUpdate)
    }
  }, [settings])

  // Calculate materials when analysis data or settings change
  useEffect(() => {
    if (!analysisData) return
    
    // Extract relevant data from analysis
    const walls = analysisData.walls || []
    const corners = analysisData.corners || []
    const icfMetrics = analysisData.icf_metrics || {}
    const metadata = analysisData.metadata || {}
    
    // Get wall dimensions
    const totalLinearFeet = icfMetrics.total_linear_feet || 0
    const totalCorners = icfMetrics.total_corners || 0
    const wallHeightFeet = parseFloat(icfMetrics.assumptions?.wall_height_feet || metadata.wall_height || "8.0")
    const wallAreaSqft = icfMetrics.wall_area_sqft || 0
    
    // Calculate panel requirements
    const panelWidthFeet = settings.panelWidth / 12
    const panelHeightFeet = settings.panelHeight / 12
    const panelAreaSqft = panelWidthFeet * panelHeightFeet
    
    // Standard panels (excluding corners)
    const cornerPanelLinearFeet = totalCorners * 2 // Assuming 2 linear feet per corner
    const standardPanelLinearFeet = totalLinearFeet - cornerPanelLinearFeet
    const standardPanelsCount = Math.ceil(standardPanelLinearFeet / panelWidthFeet)
    const standardPanelsArea = standardPanelsCount * panelAreaSqft
    
    // Corner panels
    const cornerPanelsCount = totalCorners
    
    // Calculate rebar requirements
    // Vertical rebar
    const verticalRebarCount = Math.ceil(totalLinearFeet * 12 / settings.verticalRebarSpacing)
    const verticalRebarLengthFeet = verticalRebarCount * wallHeightFeet
    
    // Horizontal rebar
    const horizontalRebarCount = settings.horizontalRebarCourses
    const horizontalRebarLengthFeet = horizontalRebarCount * totalLinearFeet
    
    // Calculate concrete volume
    // Using the formula: 0.016 cubic yards per square foot of wall for 6" core
    // Adjust for different core widths
    const concreteFactor = settings.concreteCore / 6 * 0.016
    const concreteVolumeCuYd = wallAreaSqft * concreteFactor
    const concreteVolumeWithWaste = concreteVolumeCuYd * (1 + settings.concreteWasteFactor / 100)
    
    // Calculate accessories
    // Form alignment systems
    const formAlignmentCount = Math.ceil(totalLinearFeet / settings.formAlignmentSpacing)
    
    // Bracing
    const bracingCount = Math.ceil(wallHeightFeet / settings.bracingSpacing * totalLinearFeet / 20)
    
    // Window/door bucks - estimate as 10% of total linear feet if enabled
    const windowDoorBucksLinearFeet = settings.windowDoorBucks ? totalLinearFeet * 0.1 : 0
    
    // Fastening strips - estimate as 1 per 4 square feet of wall if enabled
    const fasteningStripsCount = settings.fasteningStrips ? Math.ceil(wallAreaSqft / 4) : 0
    
    // Calculate labor estimates
    // Installation rate: 500-800 sq ft of wall area per crew day (3-4 person crew)
    const crewDays = wallAreaSqft / 650 // Using average of 650 sq ft per day
    
    // Pour rate: Typically 4' vertical lift per hour
    const pourTimeHours = wallHeightFeet / 4
    
    // Create materials calculation
    const newMaterials = {
      standardPanels: {
        count: standardPanelsCount,
        areaSqft: standardPanelsArea
      },
      cornerPanels: {
        count: cornerPanelsCount
      },
      verticalRebar: {
        type: settings.verticalRebarType,
        count: verticalRebarCount,
        lengthFeet: verticalRebarLengthFeet
      },
      horizontalRebar: {
        type: settings.horizontalRebarType,
        count: horizontalRebarCount,
        lengthFeet: horizontalRebarLengthFeet
      },
      concrete: {
        strengthPsi: settings.concretePsi,
        slumpInches: settings.concreteSlump,
        volumeCuYd: concreteVolumeCuYd,
        volumeWithWaste: concreteVolumeWithWaste
      },
      formAlignmentSystems: {
        count: formAlignmentCount
      },
      bracing: {
        count: bracingCount
      },
      windowDoorBucks: {
        linearFeet: windowDoorBucksLinearFeet
      },
      fasteningStrips: {
        count: fasteningStripsCount
      },
      labor: {
        crewDays: crewDays,
        pourTimeHours: pourTimeHours
      }
    }
    
    // Update materials state and notify parent
    setMaterials(newMaterials)
    onCalculation?.(newMaterials)
  }, [analysisData, settings, onCalculation])

  // Handle settings change
  const handleSettingsChange = (newSettings: ICFSettings) => {
    setSettings(newSettings)
  }

  if (loading) {
    return <div className="p-4 text-center">Loading ICF materials data...</div>
  }

  if (error) {
    return <div className="p-4 text-center text-red-500">{error}</div>
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>ICF Materials Quotation</CardTitle>
        <CardDescription>
          Comprehensive materials list for ICF construction based on foundation analysis
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="summary">
          <TabsList className="bg-secondary border border-border/40">
            <TabsTrigger value="summary" className="text-sm">
              Materials Summary
            </TabsTrigger>
            <TabsTrigger value="settings" className="text-sm">
              Calculation Settings
            </TabsTrigger>
          </TabsList>

          <TabsContent value="summary" className="mt-4">
            {materials && <ICFMaterialsSummary materials={materials} />}
          </TabsContent>

          <TabsContent value="settings" className="mt-4">
            <ICFCalculationSettings 
              settings={settings} 
              onSettingsChange={handleSettingsChange} 
            />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
