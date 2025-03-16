"use client"

import { useState, useEffect } from "react"
import { ICFSettings } from "./icf-materials-quotation"
import { Card, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { InfoIcon } from "lucide-react"

interface ICFCalculationSettingsProps {
  settings: ICFSettings
  onSettingsChange: (settings: ICFSettings) => void
}

export function ICFCalculationSettings({ settings, onSettingsChange }: ICFCalculationSettingsProps) {
  const [localSettings, setLocalSettings] = useState<ICFSettings>(settings)
  const [recommendations, setRecommendations] = useState<Record<string, string>>({})
  
  // Generate recommendations based on current settings
  useEffect(() => {
    const newRecommendations: Record<string, string> = {}
    
    // Wall height-based recommendations
    const wallHeightBasedRecommendations = () => {
      // Vertical rebar recommendations
      if (localSettings.concreteCore >= 8 && localSettings.verticalRebarType !== "#5") {
        newRecommendations.verticalRebarType = "For walls with 8\" or larger cores, #5 rebar is recommended"
      }
      
      // Vertical spacing recommendations
      if (localSettings.concreteCore >= 8 && localSettings.verticalRebarSpacing > 24) {
        newRecommendations.verticalRebarSpacing = "For thicker walls, spacing should not exceed 24\""
      }
      
      // Horizontal courses recommendations
      const recommendedCourses = Math.ceil(localSettings.concreteCore / 2)
      if (localSettings.horizontalRebarCourses < recommendedCourses) {
        newRecommendations.horizontalRebarCourses = `For ${localSettings.concreteCore}\" core walls, at least ${recommendedCourses} courses are recommended`
      }
      
      // Bracing recommendations
      if (localSettings.bracingSpacing > 5 && localSettings.concreteCore >= 8) {
        newRecommendations.bracingSpacing = "For thicker walls, bracing every 4-5 feet is recommended"
      }
      
      // Concrete PSI recommendations
      if (localSettings.concreteCore >= 8 && localSettings.concretePsi < 3500) {
        newRecommendations.concretePsi = "For thicker walls, at least 3,500 PSI concrete is recommended"
      }
      
      // Concrete slump recommendations
      if (localSettings.concreteCore >= 8 && localSettings.concreteSlump < 5) {
        newRecommendations.concreteSlump = "For thicker walls, a slump of 5-6 inches is recommended"
      }
    }
    
    wallHeightBasedRecommendations()
    
    setRecommendations(newRecommendations)
  }, [localSettings])

  // Handle input changes
  const handleInputChange = (field: keyof ICFSettings, value: any) => {
    const newSettings = { ...localSettings, [field]: value }
    setLocalSettings(newSettings)
  }
  
  // Handle number input changes
  const handleNumberChange = (field: keyof ICFSettings, value: string) => {
    const numValue = parseFloat(value)
    if (!isNaN(numValue)) {
      handleInputChange(field, numValue)
    }
  }
  
  // Apply settings
  const applySettings = () => {
    onSettingsChange(localSettings)
  }
  
  // Reset to defaults
  const resetToDefaults = () => {
    setLocalSettings({
      panelWidth: 16,
      panelHeight: 48,
      formThickness: 5,
      concreteCore: 6,
      
      verticalRebarType: "#4",
      verticalRebarSpacing: 24,
      horizontalRebarType: "#4",
      horizontalRebarCourses: 3,
      
      concretePsi: 3500,
      concreteSlump: 5.5,
      concreteWasteFactor: 10,
      
      formAlignmentSpacing: 6,
      bracingSpacing: 5,
      windowDoorBucks: true,
      fasteningStrips: true
    })
  }
  
  return (
    <div className="space-y-6">
      <Accordion type="multiple" defaultValue={["panel-specs", "rebar", "concrete", "accessories"]}>
        {/* Panel Specifications */}
        <AccordionItem value="panel-specs">
          <AccordionTrigger className="text-base font-medium">ICF Panel Specifications</AccordionTrigger>
          <AccordionContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-2">
              <div className="space-y-2">
                <Label htmlFor="panel-width">Standard Panel Width (inches)</Label>
                <Input
                  id="panel-width"
                  type="number"
                  value={localSettings.panelWidth}
                  onChange={(e) => handleNumberChange("panelWidth", e.target.value)}
                />
                <p className="text-xs text-muted-foreground">Standard width is 16"</p>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="panel-height">Standard Panel Height (inches)</Label>
                <Input
                  id="panel-height"
                  type="number"
                  value={localSettings.panelHeight}
                  onChange={(e) => handleNumberChange("panelHeight", e.target.value)}
                />
                <p className="text-xs text-muted-foreground">Standard height is 48"</p>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="form-thickness">Form Thickness (inches)</Label>
                <Input
                  id="form-thickness"
                  type="number"
                  value={localSettings.formThickness}
                  onChange={(e) => handleNumberChange("formThickness", e.target.value)}
                />
                <p className="text-xs text-muted-foreground">Typically 5" (2.5" on each side)</p>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="concrete-core">Concrete Core Width (inches)</Label>
                <Select
                  value={localSettings.concreteCore.toString()}
                  onValueChange={(value) => handleInputChange("concreteCore", parseInt(value, 10))}
                >
                  <SelectTrigger id="concrete-core">
                    <SelectValue placeholder="Select core width" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="6">6" Core (Most Common)</SelectItem>
                    <SelectItem value="8">8" Core</SelectItem>
                    <SelectItem value="10">10" Core</SelectItem>
                    <SelectItem value="12">12" Core</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">6" is most common for residential</p>
                <p className="text-xs text-muted-foreground mt-1">
                  <strong>Note:</strong> Changing core width will automatically adjust rebar and concrete requirements
                </p>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
        
        {/* Rebar Requirements */}
        <AccordionItem value="rebar">
          <AccordionTrigger className="text-base font-medium">Rebar Requirements</AccordionTrigger>
          <AccordionContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-2">
              <div className="space-y-2">
                <Label htmlFor="vertical-rebar-type">Vertical Rebar Type</Label>
                <Select
                  value={localSettings.verticalRebarType}
                  onValueChange={(value) => handleInputChange("verticalRebarType", value)}
                >
                  <SelectTrigger id="vertical-rebar-type">
                    <SelectValue placeholder="Select rebar type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="#3">#3 (3/8" diameter)</SelectItem>
                    <SelectItem value="#4">#4 (1/2" diameter)</SelectItem>
                    <SelectItem value="#5">#5 (5/8" diameter)</SelectItem>
                    <SelectItem value="#6">#6 (3/4" diameter)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">Typically #4 or #5</p>
                {recommendations.verticalRebarType && (
                  <Alert variant="destructive" className="mt-2 py-2 bg-amber-50 border-amber-200 text-amber-800">
                    <InfoIcon className="h-4 w-4" />
                    <AlertDescription className="text-xs ml-2">
                      {recommendations.verticalRebarType}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="vertical-spacing">Vertical Rebar Spacing (inches)</Label>
                <div className="flex items-center space-x-2">
                  <Slider
                    id="vertical-spacing"
                    min={12}
                    max={36}
                    step={4}
                    value={[localSettings.verticalRebarSpacing]}
                    onValueChange={(value) => handleInputChange("verticalRebarSpacing", value[0])}
                    className="flex-1"
                  />
                  <span className="w-12 text-center">{localSettings.verticalRebarSpacing}"</span>
                </div>
                <p className="text-xs text-muted-foreground">Typically 16" to 24" on center</p>
                {recommendations.verticalRebarSpacing && (
                  <Alert variant="destructive" className="mt-2 py-2 bg-amber-50 border-amber-200 text-amber-800">
                    <InfoIcon className="h-4 w-4" />
                    <AlertDescription className="text-xs ml-2">
                      {recommendations.verticalRebarSpacing}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="horizontal-rebar-type">Horizontal Rebar Type</Label>
                <Select
                  value={localSettings.horizontalRebarType}
                  onValueChange={(value) => handleInputChange("horizontalRebarType", value)}
                >
                  <SelectTrigger id="horizontal-rebar-type">
                    <SelectValue placeholder="Select rebar type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="#3">#3 (3/8" diameter)</SelectItem>
                    <SelectItem value="#4">#4 (1/2" diameter)</SelectItem>
                    <SelectItem value="#5">#5 (5/8" diameter)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">Typically #4</p>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="horizontal-courses">Horizontal Rebar Courses</Label>
                <div className="flex items-center space-x-2">
                  <Slider
                    id="horizontal-courses"
                    min={1}
                    max={6}
                    step={1}
                    value={[localSettings.horizontalRebarCourses]}
                    onValueChange={(value) => handleInputChange("horizontalRebarCourses", value[0])}
                    className="flex-1"
                  />
                  <span className="w-12 text-center">{localSettings.horizontalRebarCourses}</span>
                </div>
                <p className="text-xs text-muted-foreground">Number of horizontal courses</p>
                {recommendations.horizontalRebarCourses && (
                  <Alert variant="destructive" className="mt-2 py-2 bg-amber-50 border-amber-200 text-amber-800">
                    <InfoIcon className="h-4 w-4" />
                    <AlertDescription className="text-xs ml-2">
                      {recommendations.horizontalRebarCourses}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
        
        {/* Concrete Specifications */}
        <AccordionItem value="concrete">
          <AccordionTrigger className="text-base font-medium">Concrete Specifications</AccordionTrigger>
          <AccordionContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-2">
              <div className="space-y-2">
                <Label htmlFor="concrete-psi">Concrete Strength (PSI)</Label>
                <Select
                  value={localSettings.concretePsi.toString()}
                  onValueChange={(value) => handleInputChange("concretePsi", parseInt(value, 10))}
                >
                  <SelectTrigger id="concrete-psi">
                    <SelectValue placeholder="Select concrete strength" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="3000">3,000 PSI</SelectItem>
                    <SelectItem value="3500">3,500 PSI</SelectItem>
                    <SelectItem value="4000">4,000 PSI</SelectItem>
                    <SelectItem value="4500">4,500 PSI</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">Typically 3,000 to 4,000 PSI</p>
                {recommendations.concretePsi && (
                  <Alert variant="destructive" className="mt-2 py-2 bg-amber-50 border-amber-200 text-amber-800">
                    <InfoIcon className="h-4 w-4" />
                    <AlertDescription className="text-xs ml-2">
                      {recommendations.concretePsi}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="concrete-slump">Concrete Slump (inches)</Label>
                <div className="flex items-center space-x-2">
                  <Slider
                    id="concrete-slump"
                    min={4}
                    max={7}
                    step={0.5}
                    value={[localSettings.concreteSlump]}
                    onValueChange={(value) => handleInputChange("concreteSlump", value[0])}
                    className="flex-1"
                  />
                  <span className="w-12 text-center">{localSettings.concreteSlump}"</span>
                </div>
                <p className="text-xs text-muted-foreground">Typically 5" to 6" for ICF</p>
                {recommendations.concreteSlump && (
                  <Alert variant="destructive" className="mt-2 py-2 bg-amber-50 border-amber-200 text-amber-800">
                    <InfoIcon className="h-4 w-4" />
                    <AlertDescription className="text-xs ml-2">
                      {recommendations.concreteSlump}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="waste-factor">Waste Factor (%)</Label>
                <div className="flex items-center space-x-2">
                  <Slider
                    id="waste-factor"
                    min={5}
                    max={20}
                    step={1}
                    value={[localSettings.concreteWasteFactor]}
                    onValueChange={(value) => handleInputChange("concreteWasteFactor", value[0])}
                    className="flex-1"
                  />
                  <span className="w-12 text-center">{localSettings.concreteWasteFactor}%</span>
                </div>
                <p className="text-xs text-muted-foreground">Recommended 10% minimum</p>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
        
        {/* Accessories */}
        <AccordionItem value="accessories">
          <AccordionTrigger className="text-base font-medium">Accessories & Installation</AccordionTrigger>
          <AccordionContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-2">
              <div className="space-y-2">
                <Label htmlFor="alignment-spacing">Form Alignment Spacing (feet)</Label>
                <div className="flex items-center space-x-2">
                  <Slider
                    id="alignment-spacing"
                    min={4}
                    max={8}
                    step={1}
                    value={[localSettings.formAlignmentSpacing]}
                    onValueChange={(value) => handleInputChange("formAlignmentSpacing", value[0])}
                    className="flex-1"
                  />
                  <span className="w-12 text-center">{localSettings.formAlignmentSpacing}'</span>
                </div>
                <p className="text-xs text-muted-foreground">Typically every 4' to 8' horizontally</p>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="bracing-spacing">Bracing Spacing (feet)</Label>
                <div className="flex items-center space-x-2">
                  <Slider
                    id="bracing-spacing"
                    min={4}
                    max={6}
                    step={0.5}
                    value={[localSettings.bracingSpacing]}
                    onValueChange={(value) => handleInputChange("bracingSpacing", value[0])}
                    className="flex-1"
                  />
                  <span className="w-12 text-center">{localSettings.bracingSpacing}'</span>
                </div>
                <p className="text-xs text-muted-foreground">Typically every 4' to 6' of wall height</p>
                {recommendations.bracingSpacing && (
                  <Alert variant="destructive" className="mt-2 py-2 bg-amber-50 border-amber-200 text-amber-800">
                    <InfoIcon className="h-4 w-4" />
                    <AlertDescription className="text-xs ml-2">
                      {recommendations.bracingSpacing}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="window-door-bucks"
                  checked={localSettings.windowDoorBucks}
                  onCheckedChange={(checked) => handleInputChange("windowDoorBucks", checked)}
                />
                <Label htmlFor="window-door-bucks">Include Window/Door Bucks</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="fastening-strips"
                  checked={localSettings.fasteningStrips}
                  onCheckedChange={(checked) => handleInputChange("fasteningStrips", checked)}
                />
                <Label htmlFor="fastening-strips">Include Fastening Strips</Label>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
      
      <div className="flex justify-end space-x-2">
        <Button variant="outline" onClick={resetToDefaults}>
          Reset to Defaults
        </Button>
        <Button onClick={applySettings}>
          Apply Settings
        </Button>
      </div>
    </div>
  )
}
