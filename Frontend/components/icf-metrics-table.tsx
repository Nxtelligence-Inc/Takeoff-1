"use client"

interface ICFMetricsTableProps {
  analysisId: string
}

export function ICFMetricsTable({ analysisId }: ICFMetricsTableProps) {
  // In a real app, this would fetch data based on the analysisId
  const metrics = {
    total_linear_feet: "150.2",
    total_corners: 8,
    wall_area_sqft: "1202.0",
    wall_thickness_feet: "0.67",
    concrete_volume_cuyd: "29.7",
    bounding_box: {
      width_feet: "38.1",
      length_feet: "40.1",
    },
    assumptions: {
      wall_height_feet: "8.0",
      standard_icf_form_width_inches: "16",
      standard_icf_form_height_inches: "48",
      rebar_horizontal_courses: 3,
      rebar_vertical_spacing_inches: 24,
    },
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-md bg-muted/50 p-3">
          <div className="text-sm text-muted-foreground">Total Linear Feet</div>
          <div className="text-2xl font-bold">{metrics.total_linear_feet}</div>
        </div>
        <div className="rounded-md bg-muted/50 p-3">
          <div className="text-sm text-muted-foreground">Total Corners</div>
          <div className="text-2xl font-bold">{metrics.total_corners}</div>
        </div>
        <div className="rounded-md bg-muted/50 p-3">
          <div className="text-sm text-muted-foreground">Wall Area (sq ft)</div>
          <div className="text-2xl font-bold">{metrics.wall_area_sqft}</div>
        </div>
        <div className="rounded-md bg-muted/50 p-3">
          <div className="text-sm text-muted-foreground">Concrete Volume (cu yd)</div>
          <div className="text-2xl font-bold">{metrics.concrete_volume_cuyd}</div>
        </div>
      </div>

      <div className="rounded-md border">
        <div className="border-b bg-muted/50 px-3 py-2 text-sm font-medium">Dimensions</div>
        <div className="p-3">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <div className="text-xs text-muted-foreground">Width</div>
              <div className="font-weight-605">{metrics.bounding_box.width_feet} ft</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Length</div>
              <div className="font-weight-605">{metrics.bounding_box.length_feet} ft</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Wall Thickness</div>
              <div className="font-weight-605">{metrics.wall_thickness_feet} ft</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Wall Height</div>
              <div className="font-weight-605">{metrics.assumptions.wall_height_feet} ft</div>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-md border">
        <div className="border-b bg-muted/50 px-3 py-2 text-sm font-medium">ICF Assumptions</div>
        <div className="p-3">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <div className="text-xs text-muted-foreground">Form Width</div>
              <div className="font-weight-605">{metrics.assumptions.standard_icf_form_width_inches}"</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Form Height</div>
              <div className="font-weight-605">{metrics.assumptions.standard_icf_form_height_inches}"</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Horizontal Rebar Courses</div>
              <div className="font-weight-605">{metrics.assumptions.rebar_horizontal_courses}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Vertical Rebar Spacing</div>
              <div className="font-weight-605">{metrics.assumptions.rebar_vertical_spacing_inches}"</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

