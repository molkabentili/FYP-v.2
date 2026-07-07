import { CheckCircle2, UploadCloud } from 'lucide-react'
import { type ChangeEvent, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Card, CardDescription, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Table, TBody, TD, TH, THead, TR } from '../components/ui/Table'
import { preprocessDataset } from '../../services/api'

type UploadPreview = {
  dataset_id: string
  file_name: string
  total_records: number
  total_columns: number
  file_size_bytes: number
  quality_score: number
}

export function UploadPage() {
  const [loadedData, setLoadedData] = useState<UploadPreview | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const persistUpload = (payload: UploadPreview, preprocessFile?: string) => {
    sessionStorage.setItem('smartseg_dataset_id', payload.dataset_id)
    sessionStorage.setItem('smartseg_upload', JSON.stringify(payload))

    if (preprocessFile) {
      sessionStorage.setItem('smartseg_preprocessed_file', preprocessFile)
    }

    setLoadedData(payload)
  }

  const handleDemoUpload = async () => {
    try {
      setLoading(true)
      setError(null)

      const payload: UploadPreview = {
        dataset_id: 'demo-local-dataset',
        file_name: 'telecom_customers_demo.csv',
        total_records: 15400,
        total_columns: 12,
        file_size_bytes: Math.round(2.8 * 1024 * 1024),
        quality_score: 96.5
      }

      persistUpload(payload)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Demo upload failed')
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      setLoading(true)
      setError(null)

      const text = await file.text()
      const rows = text.split(/\r?\n/).filter((l) => l.trim().length > 0)

      const header = rows[0] ?? ''
      const columns = header ? header.split(',').length : 0

      const datasetName = file.name.replace(/\.[^/.]+$/, '')

      // 🚀 REAL BACKEND CALL
      const preprocessResult = await preprocessDataset(file, datasetName)

      const backendFile =
        preprocessResult.output_file || preprocessResult.output_filename

      if (!backendFile) {
        throw new Error('Backend did not return a valid processed file')
      }

      sessionStorage.setItem('smartseg_preprocessed_file', backendFile)
      sessionStorage.setItem(
        'smartseg_preprocess_result',
        JSON.stringify(preprocessResult)
      )

      const payload: UploadPreview = {
        dataset_id: `local-${Date.now()}`,
        file_name: file.name,
        total_records:
          preprocessResult.cleaned_shape?.[0] ??
          Math.max(0, rows.length - 1),
        total_columns:
          preprocessResult.cleaned_shape?.[1] ?? columns,
        file_size_bytes: file.size,
        quality_score: 95.0
      }

      persistUpload(payload, backendFile)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'CSV upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container-page space-y-6">

      {/* Upload Box */}
      <Card className="brand-subtle border-dashed border-2 border-[var(--ooredoo-coral)] text-center">
        <UploadCloud className="mx-auto mb-3 text-[var(--ooredoo-red)]" size={40} />
        <CardTitle>Upload Customer CSV</CardTitle>
        <CardDescription className="mt-1">
          Drag and drop your file or use demo data.
        </CardDescription>

        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={handleFileChange}
        />

        <div className="mt-4 flex justify-center gap-3">
          <Button onClick={() => fileInputRef.current?.click()} disabled={loading}>
            {loading ? 'Processing...' : 'Choose File'}
          </Button>

          <Button variant="secondary" onClick={handleDemoUpload} disabled={loading}>
            {loading ? 'Loading...' : 'Load Demo Dataset'}
          </Button>
        </div>

        {error && <p className="mt-3 text-sm text-red-700">{error}</p>}
      </Card>

      {/* Preview */}
      {loadedData && (
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">{loadedData.file_name}</CardTitle>
              <p className="text-sm text-slate-600">
                {(loadedData.file_size_bytes / (1024 * 1024)).toFixed(2)} MB |{' '}
                {loadedData.total_columns} columns
              </p>
            </div>

            <Badge className="bg-green-100 text-green-700">
              {loadedData.quality_score}% quality
            </Badge>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg bg-gray-50 p-3">
              <p className="text-xl font-bold">
                {loadedData.total_records.toLocaleString()}
              </p>
              <p className="text-xs text-slate-600">Records</p>
            </div>

            <div className="rounded-lg bg-gray-50 p-3">
              <p className="text-xl font-bold">{loadedData.total_columns}</p>
              <p className="text-xs text-slate-600">Columns</p>
            </div>

            <div className="rounded-lg bg-gray-50 p-3">
              <p className="text-xl font-bold">
                {(loadedData.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
              </p>
              <p className="text-xs text-slate-600">File Size</p>
            </div>
          </div>

          <Link to="/configure">
            <Button className="mt-4">Proceed to Configuration</Button>
          </Link>
        </Card>
      )}

      {/* Info */}
      <Card>
        <CardTitle>Required Columns</CardTitle>

        <div className="mt-3 overflow-x-auto">
          <Table>
            <THead>
              <TR>
                <TH>Field</TH>
                <TH>Type</TH>
              </TR>
            </THead>

            <TBody>
              {[
                ['customer_id', 'String'],
                ['arpu', 'Numeric'],
                ['data_usage', 'Numeric'],
                ['voice_minutes', 'Numeric'],
                ['tenure', 'Numeric']
              ].map(([field, type]) => (
                <TR key={field}>
                  <TD>{field}</TD>
                  <TD>{type}</TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      </Card>

      {/* Quality */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="bg-green-50">
          <CardTitle className="text-base">Data Quality Checks</CardTitle>
          <ul className="mt-2 text-sm space-y-1">
            <li><CheckCircle2 size={14} className="inline mr-2" />Missing values</li>
            <li><CheckCircle2 size={14} className="inline mr-2" />Duplicates</li>
            <li><CheckCircle2 size={14} className="inline mr-2" />Outliers</li>
          </ul>
        </Card>

        <Card className="bg-blue-50">
          <CardTitle className="text-base">Auto Processing</CardTitle>
          <ul className="mt-2 text-sm space-y-1">
            <li>Normalization</li>
            <li>Imputation</li>
            <li>Encoding</li>
          </ul>
        </Card>
      </div>
    </div>
  )
}