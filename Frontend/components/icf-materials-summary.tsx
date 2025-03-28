"use client"

import { ICFMaterialsCalculation } from "./icf-materials-quotation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Download, Printer, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { generateQuotationPDF } from "@/lib/pdf-generator"
import { generateQuotationCSV } from "@/lib/csv-formatter"

interface ICFMaterialsSummaryProps {
  materials: ICFMaterialsCalculation
}

export function ICFMaterialsSummary({ materials }: ICFMaterialsSummaryProps) {
  // Format number with commas and decimal places
  const formatNumber = (num: number, decimals: number = 0) => {
    return num.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    })
  }
  
  // Handle print
  const handlePrint = () => {
    window.print()
  }
  
  // Handle PDF export
  const handlePdfExport = async () => {
    try {
      const doc = await generateQuotationPDF(materials, {
        drawingName: "Materials Summary",
        projectId: "Current Project",
        timestamp: new Date().toISOString()
      });
      doc.save("materials-quotation.pdf");
    } catch (error) {
      // Show alert instead of logging to console
      alert('Error generating PDF. Please try again.');
    }
  };

  // Handle CSV export
  const handleCsvExport = () => {
    const csvContent = generateQuotationCSV(materials);
    
    // Create blob and trigger download
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "materials-quotation.csv");
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">ICF Materials Summary</h3>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm" onClick={handlePdfExport}>
            <FileText className="mr-2 h-4 w-4" />
            Export PDF
          </Button>
          <Button variant="outline" size="sm" onClick={handleCsvExport}>
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
          <Button variant="outline" size="sm" onClick={handlePrint}>
            <Printer className="mr-2 h-4 w-4" />
            Print
          </Button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Panel Requirements */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Panel Requirements</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Standard Panels:</span>
                <span className="font-medium">{formatNumber(materials.standardPanels.count)} panels</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Standard Panel Area:</span>
                <span className="font-medium">{formatNumber(materials.standardPanels.areaSqft, 1)} sq ft</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Corner Panels:</span>
                <span className="font-medium">{formatNumber(materials.cornerPanels.count)} panels</span>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Rebar Requirements */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Rebar Requirements</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Vertical Rebar:</span>
                  <span className="font-medium">{materials.verticalRebar.type}</span>
                </div>
                <div className="flex justify-between pl-4">
                  <span className="text-muted-foreground">Count:</span>
                  <span className="font-medium">{formatNumber(materials.verticalRebar.count)} pieces</span>
                </div>
                <div className="flex justify-between pl-4">
                  <span className="text-muted-foreground">Total Length:</span>
                  <span className="font-medium">{formatNumber(materials.verticalRebar.lengthFeet, 1)} linear ft</span>
                </div>
              </div>
              
              <Separator />
              
              <div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Horizontal Rebar:</span>
                  <span className="font-medium">{materials.horizontalRebar.type}</span>
                </div>
                <div className="flex justify-between pl-4">
                  <span className="text-muted-foreground">Courses:</span>
                  <span className="font-medium">{formatNumber(materials.horizontalRebar.count)}</span>
                </div>
                <div className="flex justify-between pl-4">
                  <span className="text-muted-foreground">Total Length:</span>
                  <span className="font-medium">{formatNumber(materials.horizontalRebar.lengthFeet, 1)} linear ft</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Concrete Requirements */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Concrete Requirements</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Strength:</span>
                <span className="font-medium">{formatNumber(materials.concrete.strengthPsi)} PSI</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Slump:</span>
                <span className="font-medium">{materials.concrete.slumpInches}"</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Volume:</span>
                <span className="font-medium">{formatNumber(materials.concrete.volumeCuYd, 1)} cu yd</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Volume with Waste:</span>
                <span className="font-medium">{formatNumber(materials.concrete.volumeWithWaste, 1)} cu yd</span>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Accessories */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Accessories</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Form Alignment Systems:</span>
                <span className="font-medium">{formatNumber(materials.formAlignmentSystems.count)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Bracing:</span>
                <span className="font-medium">{formatNumber(materials.bracing.count)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Window/Door Bucks:</span>
                <span className="font-medium">{formatNumber(materials.windowDoorBucks.linearFeet, 1)} linear ft</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Fastening Strips:</span>
                <span className="font-medium">{formatNumber(materials.fasteningStrips.count)}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Labor Estimates */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Labor Estimates</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Estimated Crew Days:</span>
              <span className="font-medium">{formatNumber(materials.labor.crewDays, 1)} days (3-4 person crew)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Estimated Pour Time:</span>
              <span className="font-medium">{formatNumber(materials.labor.pourTimeHours, 1)} hours</span>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <div className="text-sm text-muted-foreground">
        <p>Note: These calculations are estimates based on industry standards and the provided foundation plan analysis. Actual material requirements may vary based on specific project conditions and local building codes.</p>
      </div>
    </div>
  )
}
