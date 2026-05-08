"use client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { X } from "lucide-react"

export function AdvancedFilterPanel({ filters, onFiltersChange }) {
  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters }
    if (value === "" || value === null) {
      delete newFilters[key]
    } else {
      newFilters[key] = value
    }
    onFiltersChange(newFilters)
  }

  const handleClearAll = () => {
    onFiltersChange({})
  }

  return (
    <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="minRecords">Min Records</Label>
          <Input
            id="minRecords"
            type="number"
            placeholder="0"
            value={filters.minRecords || ""}
            onChange={(e) => handleFilterChange("minRecords", e.target.value ? Number.parseInt(e.target.value) : "")}
          />
        </div>
        <div>
          <Label htmlFor="maxRecords">Max Records</Label>
          <Input
            id="maxRecords"
            type="number"
            placeholder="No limit"
            value={filters.maxRecords || ""}
            onChange={(e) => handleFilterChange("maxRecords", e.target.value ? Number.parseInt(e.target.value) : "")}
          />
        </div>
        <div>
          <Label htmlFor="minTime">Min Execution Time (ms)</Label>
          <Input
            id="minTime"
            type="number"
            placeholder="0"
            value={filters.minExecutionTime || ""}
            onChange={(e) =>
              handleFilterChange("minExecutionTime", e.target.value ? Number.parseInt(e.target.value) : "")
            }
          />
        </div>
        <div>
          <Label htmlFor="maxTime">Max Execution Time (ms)</Label>
          <Input
            id="maxTime"
            type="number"
            placeholder="No limit"
            value={filters.maxExecutionTime || ""}
            onChange={(e) =>
              handleFilterChange("maxExecutionTime", e.target.value ? Number.parseInt(e.target.value) : "")
            }
          />
        </div>
      </div>

      {Object.keys(filters).length > 0 && (
        <div className="flex items-center justify-between pt-2 border-t">
          <span className="text-sm text-muted-foreground">{Object.keys(filters).length} filter(s) applied</span>
          <Button variant="ghost" size="sm" onClick={handleClearAll} className="gap-1">
            <X className="h-4 w-4" />
            Clear All
          </Button>
        </div>
      )}
    </div>
  )
}
