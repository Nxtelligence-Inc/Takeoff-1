import { ICFMaterialsCalculation } from "@/components/icf-materials-quotation"

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

export function generateQuotationCSV(
  materials: ICFMaterialsCalculation,
  metadata?: QuotationMetadata
) {
  const headerInfo = metadata ? [
    `ICF Materials Quotation - ${metadata.drawingName}`,
    `Project: ${metadata.projectId}`,
    `Date: ${new Date(metadata.timestamp).toLocaleDateString()}`,
    "",
  ] : [
    "ICF Materials Quotation",
    `Date: ${new Date().toLocaleDateString()}`,
    "",
  ];

  const csvContent = [
    ...headerInfo,
    // Panel Requirements Section
    "Panel Requirements",
    "Item,Quantity,Unit,Notes",
    `Standard Panels,${formatNumber(materials.standardPanels.count)},,Straight wall sections`,
    `Standard Panel Area,${formatNumber(materials.standardPanels.areaSqft, 1)},sq ft,Total coverage area`,
    `Corner Panels,${formatNumber(materials.cornerPanels.count)},,90-degree corners`,
    "",
    // Rebar Requirements Section
    "Rebar Requirements",
    "Type,Specification,Quantity,Length,Notes",
    `Vertical Rebar,${materials.verticalRebar.type},${formatNumber(materials.verticalRebar.count)} pieces,${formatNumber(materials.verticalRebar.lengthFeet, 1)} linear ft,Primary wall reinforcement`,
    `Horizontal Rebar,${materials.horizontalRebar.type},${formatNumber(materials.horizontalRebar.count)} courses,${formatNumber(materials.horizontalRebar.lengthFeet, 1)} linear ft,Lateral support`,
    "",
    // Concrete Requirements Section
    "Concrete Requirements",
    "Specification,Value,Unit,Notes",
    `Strength,${formatNumber(materials.concrete.strengthPsi)},PSI,Minimum required strength`,
    `Slump,${materials.concrete.slumpInches},inches,Workability measure`,
    `Base Volume,${formatNumber(materials.concrete.volumeCuYd, 1)},cu yd,Required volume`,
    `Volume with Waste,${formatNumber(materials.concrete.volumeWithWaste, 1)},cu yd,Includes ${formatNumber((materials.concrete.volumeWithWaste / materials.concrete.volumeCuYd - 1) * 100, 1)}% waste factor`,
    "",
    // Accessories Section
    "Accessories",
    "Item,Quantity,Unit,Notes",
    `Form Alignment Systems,${formatNumber(materials.formAlignmentSystems.count)},,Wall straightness control`,
    `Bracing,${formatNumber(materials.bracing.count)},,Temporary support`,
    `Window/Door Bucks,${formatNumber(materials.windowDoorBucks.linearFeet, 1)},linear ft,Opening framing`,
    `Fastening Strips,${formatNumber(materials.fasteningStrips.count)},,Attachment points`,
    "",
    // Labor Estimates Section
    "Labor Estimates",
    "Type,Duration,Unit,Notes",
    `Crew Installation,${formatNumber(materials.labor.crewDays, 1)},days,3-4 person crew`,
    `Concrete Pour,${formatNumber(materials.labor.pourTimeHours, 1)},hours,Standard conditions`,
    "",
    // Notes Section
    "Notes",
    "- All quantities are estimates based on standard industry practices",
    "- Actual material requirements may vary based on site conditions",
    "- Local building codes may require modifications to these specifications",
    "- Consult with local ICF installer for region-specific requirements",
    "- Material quantities should be verified before ordering"
  ].join("\n");

  return csvContent;
}
