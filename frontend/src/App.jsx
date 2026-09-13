import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowDownToLine,
  ArrowUpRight,
  Boxes,
  CircleCheck,
  Clock3,
  Droplets,
  Hospital,
  MapPin,
  RefreshCw,
  ShieldAlert,
  Truck,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { API_BASE_URL } from "./config";

const STATUS_ORDER = ["CRITICAL", "WARNING", "MONITOR", "SAFE"];
const STATUS_COLORS = {
  CRITICAL: "#e65f5c",
  WARNING: "#eea63a",
  MONITOR: "#3d8ca8",
  SAFE: "#35a47a",
};

const numberFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return numberFormat.format(Number(value));
}

function formatDays(value) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "No stockout forecast";
  return `${formatNumber(value)} days`;
}

function StatusBadge({ status }) {
  return <span className={`status-badge ${String(status).toLowerCase()}`}>{status}</span>;
}

function SectionHeading({ eyebrow, title, detail, action }) {
  return (
    <div className="section-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        {detail && <p className="section-detail">{detail}</p>}
      </div>
      {action}
    </div>
  );
}

function EmptyState({ children = "No records to display." }) {
  return <div className="empty-state">{children}</div>;
}

function App() {
  const [summary, setSummary] = useState(null);
  const [shortages, setShortages] = useState([]);
  const [criticalShortages, setCriticalShortages] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [filterStatus, setFilterStatus] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  async function loadDashboard() {
    setLoading(true);
    setError(false);
    try {
      const responses = await Promise.all([
        fetch(`${API_BASE_URL}/summary`),
        fetch(`${API_BASE_URL}/shortages`),
        fetch(`${API_BASE_URL}/shortages/critical`),
        fetch(`${API_BASE_URL}/redistribution`),
      ]);
      if (responses.some((response) => !response.ok)) throw new Error("API request failed");
      const [summaryData, shortagesData, criticalData, recommendationsData] = await Promise.all(
        responses.map((response) => response.json()),
      );
      setSummary(summaryData);
      setShortages(shortagesData);
      setCriticalShortages(criticalData);
      setRecommendations(recommendationsData);
      setLastUpdated(new Date());
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const filteredShortages = useMemo(
    () => filterStatus === "ALL" ? shortages : shortages.filter((row) => row.status === filterStatus),
    [filterStatus, shortages],
  );

  const priorityAlert = useMemo(
    () => [...criticalShortages].sort((left, right) => (left.days_until_stockout ?? Infinity) - (right.days_until_stockout ?? Infinity))[0],
    [criticalShortages],
  );

  const priorityRecommendation = useMemo(() => {
    if (!priorityAlert) return null;
    return recommendations
      .filter((row) => row.destination_hospital_id === priorityAlert.hospital_id && row.medicine_id === priorityAlert.medicine_id)
      .sort((left, right) => right.recommendation_score - left.recommendation_score)[0];
  }, [priorityAlert, recommendations]);

  const statusData = useMemo(
    () => STATUS_ORDER.map((status) => ({ name: status, value: shortages.filter((row) => row.status === status).length })),
    [shortages],
  );

  const medicineData = useMemo(() => {
    const medicineTotals = shortages
      .filter((row) => row.shortage_quantity > 0)
      .reduce((totals, row) => {
        totals[row.medicine_name] = (totals[row.medicine_name] || 0) + row.shortage_quantity;
        return totals;
      }, {});
    return Object.entries(medicineTotals)
      .map(([name, shortage]) => ({ name: name.length > 19 ? `${name.slice(0, 17)}...` : name, shortage }))
      .sort((left, right) => right.shortage - left.shortage)
      .slice(0, 5);
  }, [shortages]);

  const recommendationData = useMemo(
    () => [...recommendations]
      .sort((left, right) => right.recommendation_score - left.recommendation_score)
      .slice(0, 5)
      .map((row) => ({
        name: `${row.destination_hospital_id} <- ${row.source_hospital_id}`,
        score: row.recommendation_score,
      })),
    [recommendations],
  );

  const summaryCards = summary ? [
    { label: "Total hospitals", value: summary.total_hospitals, icon: Hospital, tone: "blue" },
    { label: "Total medicines", value: summary.total_medicines, icon: Droplets, tone: "teal" },
    { label: "Critical shortages", value: summary.critical_shortages, icon: ShieldAlert, tone: "coral" },
    { label: "Warning cases", value: summary.warning_shortages, icon: AlertTriangle, tone: "amber" },
    { label: "Safe cases", value: summary.safe_cases, icon: CircleCheck, tone: "green" },
    { label: "Redistribution recommendations", value: summary.total_redistribution_recommendations, icon: Truck, tone: "violet" },
  ] : [];

  return (
    <div className="app-shell">
      <aside className="side-rail">
        <div className="brand-lockup">
          <div className="brand-mark"><Activity size={21} strokeWidth={2.5} /></div>
          <div><strong>MedRipple</strong><span>Operations console</span></div>
        </div>
        <div className="rail-rule" />
        <nav className="rail-nav" aria-label="Dashboard sections">
          <a className="active" href="#overview"><Activity size={16} /> Overview</a>
          <a href="#shortages"><ShieldAlert size={16} /> Shortage watch</a>
          <a href="#redistribution"><Truck size={16} /> Redistribution</a>
        </nav>
        <div className="rail-footer">
          <div className="live-dot" />
          <div><span>Prototype status</span><strong>Data-connected</strong></div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar" id="overview">
          <div>
            <p className="kicker">Supply intelligence / 06</p>
            <h1>Medicine availability, at a glance.</h1>
            <p className="subtitle">AI-Powered Medicine Shortage Prediction &amp; Redistribution</p>
          </div>
          <button className="refresh-button" onClick={loadDashboard} disabled={loading} title="Refresh dashboard data">
            <RefreshCw size={16} className={loading ? "spin" : ""} />
            {loading ? "Refreshing" : "Refresh data"}
          </button>
        </header>

        {error && <div className="api-error" role="alert"><AlertTriangle size={18} /> Backend API is unavailable. Start the FastAPI server and refresh.</div>}
        {loading && !summary ? <div className="loading-panel"><div className="loader" /> Loading dashboard data...</div> : (
          <>
            {priorityAlert && <section className="priority-alert" aria-label="Priority alert">
              <div className="alert-icon"><ShieldAlert size={25} /></div>
              <div className="alert-copy">
                <p className="alert-label">Priority alert <span>CRITICAL SHORTAGE</span></p>
                <h2>{priorityAlert.medicine_name}</h2>
                <p><strong>{priorityAlert.hospital_name}</strong> may run out in <strong>{formatDays(priorityAlert.days_until_stockout)}</strong>.</p>
              </div>
              <div className="alert-action">
                <span>Recommended action</span>
                <strong>{priorityRecommendation ? `Transfer ${formatNumber(priorityRecommendation.recommended_transfer)} units from ${priorityRecommendation.source_hospital_id}.` : `${formatNumber(priorityAlert.shortage_quantity)} units needed`}</strong>
                <a href="#redistribution">View transfer options <ArrowUpRight size={14} /></a>
              </div>
            </section>}

            <section className="summary-grid" aria-label="Summary metrics">
              {summaryCards.map(({ label, value, icon: Icon, tone }) => <div className={`summary-card ${tone}`} key={label}>
                <div className="summary-icon"><Icon size={18} /></div>
                <div><span>{label}</span><strong>{formatNumber(value)}</strong></div>
              </div>)}
            </section>

            <section className="charts-grid" aria-label="Dashboard charts">
              <div className="panel chart-panel">
                <SectionHeading eyebrow="Status mix" title="Shortage distribution" detail="Current inventory health across all tracked items" />
                {shortages.length ? <div className="donut-layout">
                  <ResponsiveContainer width="52%" height={195}><PieChart>
                    <Pie data={statusData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={78} paddingAngle={3} stroke="none">
                      {statusData.map((entry) => <Cell key={entry.name} fill={STATUS_COLORS[entry.name]} />)}
                    </Pie>
                    <Tooltip formatter={(value) => [`${value} cases`, "Count"]} />
                  </PieChart></ResponsiveContainer>
                  <div className="chart-legend">{statusData.map((entry) => <div key={entry.name}><i style={{ background: STATUS_COLORS[entry.name] }} /> <span>{entry.name}</span><strong>{entry.value}</strong></div>)}</div>
                </div> : <EmptyState />}
              </div>
              <div className="panel chart-panel">
                <SectionHeading eyebrow="Exposure" title="Top medicines with shortage" detail="Units below the seven-day safety level" />
                {medicineData.length ? <ResponsiveContainer width="100%" height={205}><BarChart data={medicineData} layout="vertical" margin={{ left: 4, right: 20, top: 4, bottom: 4 }}>
                  <CartesianGrid horizontal={false} stroke="#e4ebe8" />
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="name" width={125} tick={{ fill: "#62747b", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(value) => [`${formatNumber(value)} units`, "Shortage"]} cursor={{ fill: "#f2f6f4" }} />
                  <Bar dataKey="shortage" fill="#e65f5c" radius={[0, 4, 4, 0]} barSize={18} />
                </BarChart></ResponsiveContainer> : <EmptyState />}
              </div>
              <div className="panel chart-panel recommendations-chart">
                <SectionHeading eyebrow="Action queue" title="Recommendation priority" detail="Highest scoring transfer paths" />
                {recommendationData.length ? <ResponsiveContainer width="100%" height={205}><BarChart data={recommendationData} margin={{ left: 2, right: 10, top: 4, bottom: 4 }}>
                  <CartesianGrid vertical={false} stroke="#e4ebe8" />
                  <XAxis dataKey="name" tick={{ fill: "#62747b", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: "#62747b", fontSize: 10 }} axisLine={false} tickLine={false} width={28} />
                  <Tooltip formatter={(value) => [`${formatNumber(value)} / 100`, "Score"]} />
                  <Bar dataKey="score" fill="#357d91" radius={[4, 4, 0, 0]} barSize={30} />
                </BarChart></ResponsiveContainer> : <EmptyState />}
              </div>
            </section>

            <section className="panel table-panel" id="shortages">
              <SectionHeading eyebrow="Immediate attention" title="Critical shortages" detail={`${criticalShortages.length} cases need urgent review`} action={<a className="text-link" href="#all-shortages">View all shortages <ArrowDownToLine size={14} /></a>} />
              <ShortageTable rows={criticalShortages} critical />
            </section>

            <section className="panel table-panel" id="all-shortages">
              <SectionHeading eyebrow="Inventory watch" title="All shortages" detail="Filter the current stock outlook by status" action={<select className="filter-select" value={filterStatus} onChange={(event) => setFilterStatus(event.target.value)} aria-label="Filter shortages by status"><option value="ALL">All statuses</option>{STATUS_ORDER.map((status) => <option key={status} value={status}>{status}</option>)}</select>} />
              <ShortageTable rows={filteredShortages} />
            </section>

            <section className="panel table-panel" id="redistribution">
              <SectionHeading eyebrow="Network response" title="Redistribution recommendations" detail={`${recommendations.length} transfer paths ranked by urgency, surplus, and distance`} />
              <RecommendationTable rows={recommendations} />
            </section>
          </>
        )}
        <footer className="page-footer"><span><Droplets size={14} /> MedRipple</span><span>Synthetic hackathon prototype · No patient data</span>{lastUpdated && <span>Updated {lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>}</footer>
      </main>
    </div>
  );
}

function ShortageTable({ rows, critical = false }) {
  if (!rows.length) return <EmptyState>{critical ? "No critical shortages found." : "No shortages match this filter."}</EmptyState>;
  return <div className="table-wrap"><table><thead><tr><th>Hospital</th><th>Medicine</th><th>Current stock</th><th>Daily demand</th><th>Days remaining</th><th>Risk score</th><th>Status</th></tr></thead><tbody>{rows.map((row) => <tr key={`${row.hospital_id}-${row.medicine_id}`} className={critical ? "critical-row" : ""}><td><strong>{row.hospital_id}</strong><span>{row.hospital_name}</span></td><td>{row.medicine_name}<small>{row.medicine_id}</small></td><td className="numeric">{formatNumber(row.current_stock)}</td><td className="numeric">{formatNumber(row.predicted_daily_demand)}</td><td className="numeric"><strong>{formatDays(row.days_until_stockout)}</strong></td><td className="numeric"><span className={`risk-number ${row.status.toLowerCase()}`}>{formatNumber(row.risk_score)}</span></td><td><StatusBadge status={row.status} /></td></tr>)}</tbody></table></div>;
}

function RecommendationTable({ rows }) {
  if (!rows.length) return <EmptyState>No redistribution recommendations available.</EmptyState>;
  return <div className="table-wrap"><table className="recommendation-table"><thead><tr><th>Destination</th><th>Medicine</th><th>Source</th><th>Shortage</th><th>Surplus</th><th>Transfer</th><th>Distance</th><th>Score</th><th>Reason</th></tr></thead><tbody>{rows.map((row, index) => <tr key={`${row.destination_hospital_id}-${row.medicine_id}-${row.source_hospital_id}-${index}`}><td><strong>{row.destination_hospital_id}</strong><span>{row.destination_hospital_name}</span></td><td>{row.medicine_name}</td><td><strong>{row.source_hospital_id}</strong><span>{row.source_hospital_name}</span></td><td className="numeric">{formatNumber(row.shortage_quantity)}</td><td className="numeric">{formatNumber(row.source_surplus)}</td><td className="numeric transfer-value">{formatNumber(row.recommended_transfer)}</td><td className="numeric">{row.distance_km == null ? "-" : `${formatNumber(row.distance_km)} km`}</td><td><span className="score-pill">{formatNumber(row.recommendation_score)}</span></td><td className="reason-cell">{row.reason}</td></tr>)}</tbody></table></div>;
}

export default App;