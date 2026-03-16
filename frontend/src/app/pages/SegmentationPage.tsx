import { Card, CardDescription, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { elbowData, platformMetrics, scatterData, segments, silhouetteData } from '../data/mockData'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts'

const featuresUsed = ['ARPU', 'Data Usage', 'Voice Minutes', 'Tenure', 'SMS Count', 'Payment Score', 'Complaint Count']

export function SegmentationPage() {
  return (
    <div className="space-y-4 pt-4">
      <div className="grid gap-3 md:grid-cols-4">
        {[
          ['Optimal Clusters', platformMetrics.optimalClusters, 'bg-blue-50 text-blue-700'],
          ['Model Accuracy', `${platformMetrics.modelAccuracy}%`, 'bg-green-50 text-green-700'],
          ['Silhouette Score', platformMetrics.silhouetteScore, 'bg-purple-50 text-purple-700'],
          ['Total Customers', platformMetrics.totalCustomers.toLocaleString(), 'bg-orange-50 text-orange-700']
        ].map(([title, value, style]) => (
          <Card key={title as string} className={style as string}><p className="text-xs uppercase">{title as string}</p><p className="text-2xl font-bold">{value as string}</p></Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>Elbow Method</CardTitle>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={elbowData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="k" /><YAxis /><Tooltip /><Line type="monotone" dataKey="inertia" stroke="#3b82f6" strokeWidth={2} dot /></LineChart>
            </ResponsiveContainer>
          </div>
          <CardDescription>Optimal point observed at k=4.</CardDescription>
        </Card>
        <Card>
          <CardTitle>Silhouette Score Analysis</CardTitle>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={silhouetteData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="k" /><YAxis domain={[0, 1]} /><Tooltip /><Bar dataKey="score">{silhouetteData.map((entry) => <Cell key={entry.k} fill={entry.k === 4 ? '#22c55e' : '#cbd5e1'} />)}</Bar></BarChart>
            </ResponsiveContainer>
          </div>
          <CardDescription>Highest score is 0.68 at k=4.</CardDescription>
        </Card>
      </div>

      <Card>
        <CardTitle>Cluster Visualization</CardTitle>
        <div className="mt-4 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart><CartesianGrid /><XAxis dataKey="x" name="Data Usage" unit="GB" /><YAxis dataKey="y" name="ARPU" unit="$" /><Tooltip /><Legend />
              {segments.map((segment) => (
                <Scatter key={segment.id} name={segment.name} data={scatterData.filter((row) => row.segment === segment.name)} fill={segment.color} />
              ))}
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card>
        <CardTitle>Features Used</CardTitle>
        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {featuresUsed.map((feature) => <div key={feature} className="rounded-lg bg-gray-100 p-2 text-sm">✅ {feature}</div>)}
        </div>
      </Card>

      <Card>
        <CardTitle>Model Validation</CardTitle>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <div><p className="text-sm">Silhouette Score</p><p className="text-xl font-bold">0.68</p><Badge className="bg-green-100 text-green-700">Good</Badge></div>
          <div><p className="text-sm">Davies-Bouldin Index</p><p className="text-xl font-bold">0.72</p><Badge className="bg-blue-100 text-blue-700">Excellent</Badge></div>
          <div><p className="text-sm">Calinski-Harabasz</p><p className="text-xl font-bold">3847.2</p><Badge className="bg-purple-100 text-purple-700">Strong</Badge></div>
        </div>
        <CardDescription className="mt-2">Validation confirms statistically robust segment separation for telecom marketing use.</CardDescription>
      </Card>
    </div>
  )
}