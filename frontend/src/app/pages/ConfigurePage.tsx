import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Card, CardTitle } from '../components/ui/Card'
import { Slider } from '../components/ui/Slider'
import { Switch } from '../components/ui/Switch'

const featurePool = [
  { label: 'ARPU', key: 'arpu', importance: 'High' },
  { label: 'Data Usage', key: 'data_usage', importance: 'High' },
  { label: 'Voice Minutes', key: 'voice_minutes', importance: 'Medium' },
  { label: 'Tenure', key: 'tenure', importance: 'High' },
  { label: 'SMS Count', key: 'sms_count', importance: 'Low' },
  { label: 'Payment Score', key: 'payment_score', importance: 'Medium' },
  { label: 'Complaint Count', key: 'complaint_count', importance: 'Medium' }
]

export function ConfigurePage() {
  const navigate = useNavigate()
  const [kValue, setKValue] = useState([4])
  const [autoK, setAutoK] = useState(true)
  const [normalization, setNormalization] = useState(true)
  const [handleMissing, setHandleMissing] = useState(true)
  const [outlier, setOutlier] = useState(true)
  const [scaling, setScaling] = useState(true)
  const [running, setRunning] = useState(false)
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>(featurePool.map((x) => x.key))
  const [imputation, setImputation] = useState<'median' | 'mean' | 'most_frequent'>('median')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!running) return
    const timer = setTimeout(() => navigate('/results'), 2000)
    return () => clearTimeout(timer)
  }, [running, navigate])

  const toggleFeature = (name: string) => {
    setSelectedFeatures((prev) => prev.includes(name) ? prev.filter((item) => item !== name) : [...prev, name])
  }

  const handleRun = async () => {
    const datasetId = sessionStorage.getItem('smartseg_dataset_id')
    if (!datasetId) {
      setError('No uploaded dataset found. Please upload data first.')
      return
    }

    setError(null)
    sessionStorage.setItem('smartseg_run_id', `demo-run-${Date.now()}`)
    setRunning(true)
  }

  return (
    <div className="container-page space-y-6">
      <Card>
        <CardTitle>Algorithm Configuration</CardTitle>
        <div className="mt-4 space-y-4">
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium">Cluster Count (k)</span>
              <span className="badge-brand">k = {kValue[0]}</span>
            </div>
            <Slider value={kValue} onValueChange={setKValue} min={2} max={8} />
          </div>
          <div className="flex items-center justify-between rounded-lg bg-gray-50 p-3">
            <div>
              <p className="text-sm font-medium">Auto-detect Optimal k</p>
              <p className="text-xs text-slate-600">Recommended using silhouette analysis</p>
            </div>
            <Switch checked={autoK} onCheckedChange={setAutoK} />
          </div>
          <div className="grid gap-3 md:grid-cols-3 text-sm">
            <p><span className="font-medium">Max Iterations:</span> 300</p>
            <p><span className="font-medium">Random State:</span> 42</p>
            <p><span className="font-medium">Algorithm:</span> K-Means++</p>
          </div>
        </div>
      </Card>

      <Card>
        <CardTitle>Preprocessing Options</CardTitle>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {[
            ['Feature Normalization', normalization, setNormalization],
            ['Handle Missing Values', handleMissing, setHandleMissing],
            ['Outlier Detection', outlier, setOutlier],
            ['Feature Scaling (StandardScaler)', scaling, setScaling]
          ].map(([label, state, setter]) => (
            <div key={label as string} className="flex items-center justify-between rounded-lg bg-gray-50 p-3">
              <span className="text-sm font-medium">{label as string}</span>
              <Switch checked={state as boolean} onCheckedChange={setter as (value: boolean) => void} />
            </div>
          ))}
        </div>
        <div className="mt-3 text-sm">
          <span className="font-medium">Imputation:</span>{' '}
          <label className="mr-3"><input type="radio" name="imputation" checked={imputation === 'median'} onChange={() => setImputation('median')} /> Median</label>
          <label className="mr-3"><input type="radio" name="imputation" checked={imputation === 'mean'} onChange={() => setImputation('mean')} /> Mean</label>
          <label><input type="radio" name="imputation" checked={imputation === 'most_frequent'} onChange={() => setImputation('most_frequent')} /> Mode</label>
        </div>
      </Card>

      <Card>
        <CardTitle>Feature Selection</CardTitle>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {featurePool.map((feature) => {
            const selected = selectedFeatures.includes(feature.key)
            return (
              <button
                key={feature.key}
                type="button"
                onClick={() => toggleFeature(feature.key)}
                className={`rounded-lg border p-3 text-left transition ${selected ? 'border-[var(--ooredoo-red)] bg-[var(--ooredoo-light-pink)]' : 'border-gray-200 bg-white'}`}
              >
                <p className="font-medium">{feature.label}</p>
                <p className="text-xs text-slate-600">Importance: {feature.importance}</p>
              </button>
            )
          })}
        </div>
      </Card>

      <Card className="brand-gradient text-white">
        {!running ? (
          <>
            <CardTitle className="text-white">Ready to Run Segmentation</CardTitle>
            <p className="mt-1 text-sm text-red-100">Estimated processing time: 30-60 seconds</p>
            <Button className="mt-4 bg-white text-[var(--ooredoo-red)]" onClick={handleRun}>Run Segmentation Analysis</Button>
          </>
        ) : (
          <>
            <CardTitle className="text-white">Running K-Means Analysis...</CardTitle>
            <ul className="mt-3 space-y-1 text-sm text-red-100">
              <li>✓ Data preprocessing complete</li>
              <li>✓ Feature normalization complete</li>
              <li>⌛ Running K-Means clustering...</li>
            </ul>
          </>
        )}
        {error && <p className="mt-3 text-sm text-red-100">{error}</p>}
      </Card>

      <Card>
        <CardTitle>Advanced Options</CardTitle>
        <div className="mt-3 grid gap-3 md:grid-cols-3 text-sm">
          <p><span className="font-medium">Convergence Tolerance:</span> 0.0001</p>
          <p><span className="font-medium">N-Init / Restarts:</span> 10</p>
          <p><span className="font-medium">Validation Method:</span> Silhouette</p>
        </div>
      </Card>
    </div>
  )
}