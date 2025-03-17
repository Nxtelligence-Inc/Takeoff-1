"use client"

import { Button } from "@/components/ui/button"
import { Download, Share2, FileText } from "lucide-react"
import { generateQuotationPDF } from "@/lib/pdf-generator"
import { generateQuotationCSV } from "@/lib/csv-formatter"
import { ICFMaterialsCalculation } from "./icf-materials-quotation"

interface AnalysisExportActionsProps {
  analysisId: string;
  drawingName: string;
  projectId: string;
  timestamp: string;
  materials: ICFMaterialsCalculation;
}

export function AnalysisExportActions({
  analysisId,
  drawingName,
  projectId,
  timestamp,
  materials
}: AnalysisExportActionsProps) {
  // Handle PDF export
  const handlePdfExport = async () => {
    try {
      const doc = await generateQuotationPDF(materials, {
        drawingName,
        projectId,
        timestamp
      });
      doc.save(`${drawingName}-quotation.pdf`);
    } catch (error) {
      // Show alert instead of logging to console
      alert('Error generating PDF. Please try again.');
    }
  };

  // Handle CSV export
  const handleCsvExport = () => {
    const csvContent = generateQuotationCSV(materials, {
      drawingName,
      projectId,
      timestamp
    });
    
    // Create blob and trigger download
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `${drawingName}-quotation.csv`);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Handle share
  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `ICF Analysis: ${drawingName}`,
          text: `ICF foundation plan analysis for ${drawingName}`,
          url: window.location.href
        });
      } catch (error) {
        // Silently handle sharing errors
      }
    } else {
      // Fallback: Copy URL to clipboard
      await navigator.clipboard.writeText(window.location.href);
      // You might want to show a toast notification here
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Button 
        variant="outline" 
        size="sm" 
        className="text-muted-foreground"
        onClick={handlePdfExport}
      >
        <FileText className="mr-2 h-4 w-4" />
        Export PDF
      </Button>
      <Button 
        variant="outline" 
        size="sm" 
        className="text-muted-foreground"
        onClick={handleCsvExport}
      >
        <Download className="mr-2 h-4 w-4" />
        Export CSV
      </Button>
      <Button 
        variant="outline" 
        size="sm" 
        className="text-muted-foreground"
        onClick={handleShare}
      >
        <Share2 className="mr-2 h-4 w-4" />
        Share
      </Button>
    </div>
  );
}
