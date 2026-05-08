'use client'

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { ArrowLeft, ArrowRight, Check } from "lucide-react"
import { ApiConfigStep } from "@/components/wizard/api-config-step"
import { ParametersStep } from "@/components/wizard/parameters-step"
import { DataMappingStep } from "@/components/wizard/data-mapping-step"
import { ScheduleStep } from "@/components/wizard/schedule-step"
import { ReviewStep } from "@/components/wizard/review-step"
import apiClient from "../../../services/apiClient.js"

const STEPS = [
  { id: 1, name: "API Configuration", description: "Configure endpoint and authentication" },
  { id: 2, name: "Parameters", description: "Set up request parameters" },
  { id: 3, name: "Data Mapping", description: "Map response fields to database" },
  { id: 4, name: "Schedule", description: "Configure automated runs" },
  { id: 5, name: "Review", description: "Review and create connection" },
]

export default function NewConnectionPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(1)
  const [wizardData, setWizardData] = useState({
    apiConfig: {
      name: "",
      description: "",
      baseUrl: "",
      method: "GET",
      headers: [],
      authType: "none",
      authConfig: {},
    },
    parameters: [],
    dataMapping: {
      selectedFields: [],
      tableName: "api_places",
    },
    schedule: {
      enabled: false,
      type: "daily",
      cronExpression: "",
    },
  })

  const updateWizardData = (step, data) => {
    setWizardData((prev) => ({
      ...prev,
      [step]: data,
    }))
  }

  const handleNext = () => {
    // Basic validation before proceeding
    if (currentStep === 1) {
      if (!wizardData.apiConfig.name?.trim()) {
        alert('Connection name is required')
        return
      }
      if (!wizardData.apiConfig.baseUrl?.trim()) {
        alert('Base URL is required')
        return
      }
    }
    
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleComplete = async () => {
    // Final validation
    if (!wizardData.apiConfig.name?.trim()) {
      alert('Connection name is required')
      return
    }
    if (!wizardData.apiConfig.baseUrl?.trim()) {
      alert('Base URL is required')
      return
    }

    try {
      const connectionData = {
        connectionId: `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: wizardData.apiConfig.name || `Connection ${Date.now()}`,
        description: wizardData.apiConfig.description,
        baseUrl: wizardData.apiConfig.baseUrl,
        method: wizardData.apiConfig.method,
        headers: wizardData.apiConfig.headers,
        authType: wizardData.apiConfig.authType,
        authConfig: wizardData.apiConfig.authConfig,
        parameters: wizardData.parameters,
        fieldMappings: wizardData.dataMapping.selectedFields,
        tableName: wizardData.dataMapping.tableName,
        schedule: wizardData.schedule,
        isActive: true
      }

      const response = await apiClient.post('/api/connections', connectionData)
      console.log('Connection create response:', response)
      console.log('Response status:', response.status)
      console.log('Response data:', response.data)
      
      // Check if response is successful (status 2xx or has data)
      if (response.status >= 200 && response.status < 300 && response.data) {
        router.push('/connections')
      } else {
        throw new Error(`Failed to save connection: ${response.status} - ${JSON.stringify(response.data)}`)
      }
    } catch (error) {
      console.error('[v0] Error saving connection:', error)
      alert('Failed to save connection. Please try again.')
    }
  }

  const progress = (currentStep / STEPS.length) * 100

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <Button variant="ghost" onClick={() => router.push('/connections')} className="mb-4 gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Connections
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">Create New API Connection</h1>
          <p className="text-muted-foreground mt-1">Follow the steps to configure your API integration</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <Progress value={progress} className="h-2 mb-4" />
          <div className="flex justify-between">
            {STEPS.map((step) => (
              <div key={step.id} className="flex flex-col items-center gap-2 flex-1 min-w-0">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                    step.id < currentStep
                      ? "bg-primary text-primary-foreground"
                      : step.id === currentStep
                        ? "bg-primary text-primary-foreground ring-4 ring-primary/20"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  {step.id < currentStep ? <Check className="h-4 w-4" /> : step.id}
                </div>
                <div className="text-center hidden sm:block max-w-full">
                  <p className="text-xs font-medium truncate">{step.name}</p>
                  <p className="text-xs text-muted-foreground truncate">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <Card>
          <CardHeader>
            <CardTitle>{STEPS[currentStep - 1].name}</CardTitle>
            <CardDescription>{STEPS[currentStep - 1].description}</CardDescription>
          </CardHeader>
          <CardContent>
            {currentStep === 1 && (
              <ApiConfigStep data={wizardData.apiConfig} onChange={(data) => updateWizardData('apiConfig', data)} />
            )}
            {currentStep === 2 && (
              <ParametersStep data={wizardData.parameters} onChange={(data) => updateWizardData('parameters', data)} />
            )}
            {currentStep === 3 && (
              <DataMappingStep
                data={wizardData.dataMapping}
                apiConfig={wizardData.apiConfig}
                parameters={wizardData.parameters}
                onChange={(data) => updateWizardData('dataMapping', data)}
              />
            )}
            {currentStep === 4 && (
              <ScheduleStep data={wizardData.schedule} onChange={(data) => updateWizardData('schedule', data)} />
            )}
            {currentStep === 5 && <ReviewStep data={wizardData} />}
          </CardContent>
        </Card>

        {/* Navigation Buttons */}
        <div className="flex flex-col sm:flex-row justify-between gap-4 mt-6">
          <Button variant="outline" onClick={handleBack} disabled={currentStep === 1} className="flex-1 sm:flex-initial">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          {currentStep < STEPS.length ? (
            <Button onClick={handleNext} className="flex-1 sm:flex-initial">
              Next
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          ) : (
            <Button onClick={handleComplete} className="flex-1 sm:flex-initial">
              <Check className="h-4 w-4 mr-2" />
              Create Connection
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
