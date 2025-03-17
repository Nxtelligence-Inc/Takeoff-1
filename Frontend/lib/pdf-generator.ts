import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { ICFMaterialsCalculation } from '@/components/icf-materials-quotation';

// Helper function to format numbers consistently
const formatNumber = (num: number, decimals: number = 0) => {
  return num.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
};

export interface QuotationMetadata {
  projectId: string;
  drawingName: string;
  timestamp: string;
}

export async function generateQuotationPDF(
  materials: ICFMaterialsCalculation,
  metadata: QuotationMetadata
) {
  // Create new PDF document
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  
  // Add logo
  try {
    const img = new Image();
    img.src = '/logos/nxtelligence-logo-black.png';
    await new Promise((resolve) => {
      img.onload = resolve;
    });
    // Calculate logo dimensions to maintain aspect ratio
    const logoWidth = 40;
    const logoHeight = (img.height * logoWidth) / img.width;
    doc.addImage(img, 'PNG', 15, 15, logoWidth, logoHeight);
  } catch (error) {
    console.error('Error loading logo:', error);
  }

  // Add header information
  doc.setFontSize(20);
  doc.text('ICF Materials Quotation', pageWidth / 2, 20, { align: 'center' });
  
  doc.setFontSize(10);
  doc.text([
    `Project: ${metadata.projectId}`,
    `Drawing: ${metadata.drawingName}`,
    `Date: ${new Date(metadata.timestamp).toLocaleDateString()}`
  ], pageWidth - 15, 25, { align: 'right' });

  // Panel Requirements
  doc.setFontSize(12);
  doc.text('Panel Requirements', 15, 50);
  autoTable(doc, {
    startY: 55,
    head: [['Item', 'Quantity', 'Unit']],
    body: [
      ['Standard Panels', formatNumber(materials.standardPanels.count), 'panels'],
      ['Standard Panel Area', formatNumber(materials.standardPanels.areaSqft, 1), 'sq ft'],
      ['Corner Panels', formatNumber(materials.cornerPanels.count), 'panels']
    ],
    theme: 'grid',
    headStyles: { fillColor: [51, 51, 51] }
  });

  // Rebar Requirements
  doc.text('Rebar Requirements', 15, doc.lastAutoTable.finalY + 15);
  autoTable(doc, {
    startY: doc.lastAutoTable.finalY + 20,
    head: [['Type', 'Specification', 'Quantity', 'Length']],
    body: [
      [
        'Vertical',
        materials.verticalRebar.type,
        formatNumber(materials.verticalRebar.count) + ' pieces',
        formatNumber(materials.verticalRebar.lengthFeet, 1) + ' linear ft'
      ],
      [
        'Horizontal',
        materials.horizontalRebar.type,
        formatNumber(materials.horizontalRebar.count) + ' courses',
        formatNumber(materials.horizontalRebar.lengthFeet, 1) + ' linear ft'
      ]
    ],
    theme: 'grid',
    headStyles: { fillColor: [51, 51, 51] }
  });

  // Concrete Requirements
  doc.text('Concrete Requirements', 15, doc.lastAutoTable.finalY + 15);
  autoTable(doc, {
    startY: doc.lastAutoTable.finalY + 20,
    head: [['Specification', 'Value']],
    body: [
      ['Strength', formatNumber(materials.concrete.strengthPsi) + ' PSI'],
      ['Slump', materials.concrete.slumpInches + '"'],
      ['Volume', formatNumber(materials.concrete.volumeCuYd, 1) + ' cu yd'],
      ['Volume with Waste', formatNumber(materials.concrete.volumeWithWaste, 1) + ' cu yd']
    ],
    theme: 'grid',
    headStyles: { fillColor: [51, 51, 51] }
  });

  // Accessories
  doc.text('Accessories', 15, doc.lastAutoTable.finalY + 15);
  autoTable(doc, {
    startY: doc.lastAutoTable.finalY + 20,
    head: [['Item', 'Quantity', 'Unit']],
    body: [
      ['Form Alignment Systems', formatNumber(materials.formAlignmentSystems.count), 'units'],
      ['Bracing', formatNumber(materials.bracing.count), 'units'],
      ['Window/Door Bucks', formatNumber(materials.windowDoorBucks.linearFeet, 1), 'linear ft'],
      ['Fastening Strips', formatNumber(materials.fasteningStrips.count), 'units']
    ],
    theme: 'grid',
    headStyles: { fillColor: [51, 51, 51] }
  });

  // Labor Estimates
  doc.text('Labor Estimates', 15, doc.lastAutoTable.finalY + 15);
  autoTable(doc, {
    startY: doc.lastAutoTable.finalY + 20,
    head: [['Type', 'Estimate', 'Notes']],
    body: [
      ['Crew Days', formatNumber(materials.labor.crewDays, 1) + ' days', '3-4 person crew'],
      ['Pour Time', formatNumber(materials.labor.pourTimeHours, 1) + ' hours', 'Standard conditions']
    ],
    theme: 'grid',
    headStyles: { fillColor: [51, 51, 51] }
  });

  // Add footer
  const footerText = 'Note: This quotation is an estimate based on industry standards and provided foundation plan analysis. ' +
    'Actual material requirements may vary based on specific project conditions and local building codes.';
  
  doc.setFontSize(8);
  const splitFooter = doc.splitTextToSize(footerText, pageWidth - 30);
  doc.text(splitFooter, pageWidth / 2, pageHeight - 20, { align: 'center' });

  return doc;
}
