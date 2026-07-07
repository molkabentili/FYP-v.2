import { Coins, Download, Mail, TrendingUp, Users } from 'lucide-react'
import { Card, CardTitle } from '../components/ui/Card'
import { Progress } from '../components/ui/Progress'
import { segments, Segment } from '../data/mockData'
import { Badge } from '../components/ui/Badge'
import { Table, TBody, TD, TH, THead, TR } from '../components/ui/Table'
import { formatAtRiskChurn, getDisplaySegments, DisplaySegment, shouldShowChurnRisk } from '../../services/segmentTransform'
import { Button } from '../components/ui/Button'
import { downloadTargetedCustomersCsv, downloadTargetedCustomersExcel, emailTargetedCustomersCsv } from '../data/exporters'

function getRunLevelLabel() {
  return 'Business Segmentation'
}

function isDisplaySegment(segment: DisplaySegment | Segment): segment is DisplaySegment {
  return 'valueSegmentName' in segment
}

export function ProfilesPage() {
  const dynamicSegments = getDisplaySegments()
  const activeSegments: (DisplaySegment | Segment)[] = dynamicSegments.length > 0 ? dynamicSegments : segments
  const runLevelLabel = getRunLevelLabel()
  const highestRevenueSegment = [...activeSegments].sort((a, b) => b.customers * b.arpu - a.customers * a.arpu)[0]
  const atRiskSegment = activeSegments.find((segment) => shouldShowChurnRisk(segment))
  const lowestArpuSegment = [...activeSegments].sort((a, b) => a.arpu - b.arpu)[0]

  return (
    <div className="space-y-4 pt-4">
      {dynamicSegments.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="text-base">Main Segmentation</CardTitle>
          <Badge className="bg-red-100 text-red-700">{runLevelLabel}</Badge>
        </div>
      )}

      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>Customer Extraction</CardTitle>
            <p className="text-sm text-slate-600">Export the full segmented customer base or one business segment.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => void downloadTargetedCustomersCsv()}><Download size={16} className="mr-2 inline" />Export All Customers CSV</Button>
            <Button variant="secondary" onClick={() => void emailTargetedCustomersCsv()}><Mail size={16} className="mr-2 inline" />Email All CSV</Button>
            <Button variant="secondary" onClick={() => void downloadTargetedCustomersExcel()}>Export All Customers Excel</Button>
          </div>
        </div>
      </Card>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {activeSegments.map((segment) => (
          <Card key={segment.id} className="border-t-4" style={{ borderTopColor: segment.color }}>
            {isDisplaySegment(segment) && <p className="text-xs font-semibold text-slate-500">Source clusters: {segment.sourceClusterIds.join(', ') || 'N/A'}</p>}
            <p className="text-sm font-semibold">{segment.name}</p>
            <p className="text-xs text-slate-600">{segment.customers.toLocaleString()} customers</p>
            <p className="mt-2 text-lg font-bold">{segment.arpu.toFixed(2)} DT/TND</p>
            <p className="text-xs text-slate-600">ARPU</p>
            <div className="mt-2"><Progress value={segment.share} color={segment.color} /></div>
            <div className="mt-3 flex flex-wrap gap-2">
              {isDisplaySegment(segment) && (
                <>
                  <Button variant="ghost" onClick={() => void downloadTargetedCustomersCsv({ segment: segment.valueSegmentName })}>Export CSV</Button>
                  <Button variant="ghost" onClick={() => void emailTargetedCustomersCsv({ segment: segment.valueSegmentName })}>Email CSV</Button>
                  <Button variant="ghost" onClick={() => void downloadTargetedCustomersExcel({ segment: segment.valueSegmentName })}>Export Excel</Button>
                </>
              )}
            </div>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {activeSegments.map((segment) => (
          <Card key={segment.id} className="border-l-4" style={{ borderLeftColor: segment.color }}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle className="text-base">{segment.name}</CardTitle>
              {shouldShowChurnRisk(segment) && (
                <Badge className={segment.churnRiskLabel === 'Low' ? 'bg-green-100 text-green-700' : segment.churnRiskLabel === 'Medium' ? 'bg-yellow-100 text-yellow-700' : segment.churnRiskLabel === 'High' ? 'bg-orange-100 text-orange-700' : 'bg-red-100 text-red-700'}>{segment.churnRiskLabel} ({formatAtRiskChurn(segment)})</Badge>
              )}
            </div>
            {isDisplaySegment(segment) && <p className="text-sm text-slate-600">Source clusters: {segment.sourceClusterIds.join(', ') || 'N/A'}</p>}
            <p className="text-sm text-slate-600">{segment.customers.toLocaleString()} customers ({segment.share}%)</p>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div className="space-y-2 text-sm">
                <p className="flex items-center gap-2"><Coins size={16} className="text-green-600" /> ARPU: {segment.arpu.toFixed(2)} DT/TND</p>
                <p className="flex items-center gap-2"><TrendingUp size={16} className="text-blue-600" /> Data: {segment.dataUsage} GB/mo</p>
                <p className="flex items-center gap-2"><TrendingUp size={16} className="text-purple-600" /> Voice: {segment.voiceMinutes} min/mo</p>
                <p className="flex items-center gap-2"><Users size={16} className="text-orange-600" /> Tenure: {segment.tenure} months</p>
                {'internationalMinutes' in segment && <p>International: {segment.internationalMinutes} min/mo</p>}
                {'complaints' in segment && <p>Complaints: {segment.complaints}</p>}
                {'satisfaction' in segment && segment.satisfaction > 0 && <p>Satisfaction: {segment.satisfaction}</p>}
              </div>
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                {segment.characteristics.map((item: string) => <li key={item}>{item}</li>)}
              </ul>
            </div>
            {'validationWarnings' in segment && segment.validationWarnings.length > 0 && (
              <div className="mt-3 rounded-md bg-yellow-50 p-3 text-sm text-yellow-800">
                {segment.validationWarnings.map((warning) => <p key={warning}>{warning}</p>)}
              </div>
            )}
          </Card>
        ))}
      </div>

      <Card>
        <CardTitle>Comparative Analysis</CardTitle>
        <div className="mt-3 overflow-x-auto">
          <Table>
            <THead><TR><TH>Source Clusters</TH><TH>Business Segment</TH><TH>Customers</TH><TH>Market Share</TH><TH>ARPU</TH><TH>Data Usage</TH><TH>Voice</TH><TH>Intl.</TH><TH>Tenure</TH><TH>Warnings</TH><TH>At Risk Churn</TH></TR></THead>
            <TBody>
              {activeSegments.map((segment) => (
                <TR key={segment.id}>
                  <TD>{isDisplaySegment(segment) ? segment.sourceClusterIds.join(', ') : segment.id}</TD><TD>{segment.name}</TD><TD>{segment.customers.toLocaleString()}</TD><TD>{segment.share}%</TD><TD>{segment.arpu.toFixed(2)} DT/TND</TD><TD>{segment.dataUsage} GB</TD><TD>{segment.voiceMinutes}</TD><TD>{'internationalMinutes' in segment ? segment.internationalMinutes : 0}</TD><TD>{segment.tenure} months</TD><TD>{'validationWarnings' in segment ? segment.validationWarnings.length : 0}</TD>
                  <TD>{shouldShowChurnRisk(segment) ? <Badge className="bg-red-50 text-red-700">{segment.churnRiskLabel} ({formatAtRiskChurn(segment)})</Badge> : 'N/A'}</TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      </Card>

      <Card>
        <CardTitle>Strategic Insights</CardTitle>
        <div className="mt-3 grid gap-3 md:grid-cols-2 text-sm">
          <div>
            <p className="font-semibold text-green-700">Revenue Opportunities</p>
            <ul className="mt-1 list-disc space-y-1 pl-5">
              <li>Prioritize {highestRevenueSegment?.name ?? 'the highest revenue segment'} for loyalty and upsell campaigns.</li>
              <li>Export each business segment for targeted bundle offers.</li>
              <li>Lift {lowestArpuSegment?.name ?? 'lower ARPU segments'} with right-sized migration paths.</li>
            </ul>
          </div>
          <div>
            <p className="font-semibold text-red-700">Risk Mitigation Priorities</p>
            <ul className="mt-1 list-disc space-y-1 pl-5">
              <li>{atRiskSegment ? `Prioritize At Risk Customers with ${formatAtRiskChurn(atRiskSegment)} churn for save offers and support follow-up.` : 'No At Risk segment is present in this clustering result.'}</li>
              <li>Review validation warnings when a segment label contradicts its metrics.</li>
              <li>Track churn-warning signals weekly by business segment.</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  )
}
