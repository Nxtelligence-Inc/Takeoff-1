"use client"

import { CheckCircle2, XCircle } from "lucide-react"

interface DatabaseConnectionStatusProps {
  type: "postgresql" | "supabase"
}

export function DatabaseConnectionStatus({ type }: DatabaseConnectionStatusProps) {
  // In a real app, this would check the actual connection status
  const isConnected = type === "postgresql" ? true : false

  return (
    <div
      className={`flex items-center gap-2 rounded-md border p-3 ${isConnected ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}`}
    >
      {isConnected ? (
        <>
          <CheckCircle2 className="h-5 w-5 text-green-500" />
          <div>
            <div className="font-medium text-green-700">Connected</div>
            <div className="text-xs text-green-600">
              {type === "postgresql"
                ? "Connected to PostgreSQL database at localhost:5432/foundation_analyzer"
                : "Connected to Supabase project"}
            </div>
          </div>
        </>
      ) : (
        <>
          <XCircle className="h-5 w-5 text-red-500" />
          <div>
            <div className="font-medium text-red-700">Not Connected</div>
            <div className="text-xs text-red-600">
              {type === "postgresql" ? "PostgreSQL connection not configured" : "Supabase connection not configured"}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

