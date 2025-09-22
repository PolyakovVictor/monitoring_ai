import React, { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { Gauge, ArrowDown, ArrowUp, Filter } from "lucide-react";

// ------------------------------
// Types aligned with your schemas
// ------------------------------

type City = {
  id: number;
  name: string;
  lat: number;
  lng: number;
};

type Station = {
  id: number;
  city_id: number;
  name: string;
};

type Pollutant = {
  id: number;
  code: string;
  description: string;
};

type MeasurementOut = {
  city: string;
  station: string;
  pollutant: string; // code
  date: string; // ISO date
  value: number;
};

type StatsOut = {
  avg: number | null;
  min: number | null;
  max: number | null;
};

// ------------------------------
// Config
// ------------------------------

// Change this to your FastAPI base URL. For local dev: http://localhost:8000
const API_BASE = (window as any).ENV_API_BASE || "/api"; // e.g. "/api" behind a proxy

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

function buildQuery(params: Record<string, any>): string {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    q.set(k, String(v));
  });
  const s = q.toString();
  return s ? `?${s}` : "";
}

// ------------------------------
// Small UI helpers
// ------------------------------

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-white rounded-2xl shadow-sm border border-gray-100 p-5 ${className}`}>{children}</div>
  );
}

function Stat({
  icon,
  label,
  value,
  hint,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number | null | undefined;
  hint?: string;
}) {
  return (
    <div className="flex items-center gap-4">
      <div className="p-3 rounded-2xl bg-gray-50 border border-gray-100">{icon}</div>
      <div>
        <div className="text-sm text-gray-500">{label}</div>
        <div className="text-2xl font-semibold">{value ?? "—"}</div>
        {hint && <div className="text-xs text-gray-400 mt-1">{hint}</div>}
      </div>
    </div>
  );
}

function SectionTitle({ title, right }: { title: string; right?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between mb-3">
      <h2 className="text-lg font-semibold">{title}</h2>
      {right}
    </div>
  );
}

// ------------------------------
// Main Component
// ------------------------------

export default function AirQualityMonitoringDashboard() {
  // Filters
  const [cityId, setCityId] = useState<number | "">("");
  const [stationId, setStationId] = useState<number | "">("");
  const [pollutantId, setPollutantId] = useState<number | "">("");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");

  // Data state
  const [cities, setCities] = useState<City[]>([]);
  const [stations, setStations] = useState<Station[]>([]);
  const [pollutants, setPollutants] = useState<Pollutant[]>([]);
  const [measurements, setMeasurements] = useState<MeasurementOut[]>([]);
  const [stats, setStats] = useState<StatsOut | null>(null);

  // Loading & error
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initial loads
  useEffect(() => {
    fetchJSON<City[]>(`${API_BASE}/cities/`).then(setCities).catch(console.error);
    fetchJSON<Pollutant[]>(`${API_BASE}/pollutants/`).then(setPollutants).catch(console.error);
  }, []);

  // Load stations when city changes
  useEffect(() => {
    setStations([]);
    setStationId("");
    if (cityId) {
      fetchJSON<Station[]>(`${API_BASE}/cities/${cityId}/stations/`).then(setStations).catch(console.error);
    }
  }, [cityId]);

  // Fetch measurements when filters change
  useEffect(() => {
    const controller = new AbortController();
    async function run() {
      setLoading(true);
      setError(null);
      try {
        const params: Record<string, any> = {
          city_id: cityId || undefined,
          station_id: stationId || undefined,
          pollutant_id: pollutantId || undefined,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
        };
        const url = `${API_BASE}/measurements/${buildQuery(params)}`;
        const data = await fetchJSON<MeasurementOut[]>(url);
        setMeasurements(data);
      } catch (e: any) {
        if (e.name !== "AbortError") setError(e.message || "Failed to load data");
      } finally {
        setLoading(false);
      }
    }
    run();
    return () => controller.abort();
  }, [cityId, stationId, pollutantId, dateFrom, dateTo]);

  // Fetch stats whenever pollutant (and optional filters) change
  useEffect(() => {
    async function run() {
      if (!pollutantId) {
        setStats(null);
        return;
      }
      const params: Record<string, any> = {
        pollutant_id: pollutantId,
        city_id: cityId || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      };
      const url = `${API_BASE}/stats/${buildQuery(params)}`;
      try {
        const s = await fetchJSON<StatsOut>(url);
        setStats(s);
      } catch (e) {
        console.error(e);
        setStats(null);
      }
    }
    run();
  }, [pollutantId, cityId, dateFrom, dateTo]);

  // Derived
  const chartData = useMemo(() => {
    // Group by date (in case multiple stations return same date)
    const byDate = new Map<string, { date: string; value: number } & Record<string, any>>();
    for (const m of measurements) {
      const d = m.date; // already yyyy-mm-dd
      if (!byDate.has(d)) byDate.set(d, { date: d, value: m.value });
      else byDate.get(d)!.value = m.value; // simplistic; could average
    }
    return Array.from(byDate.values()).sort((a, b) => (a.date < b.date ? -1 : 1));
  }, [measurements]);

  const selectedCity = useMemo(() => cities.find((c) => c.id === Number(cityId)), [cities, cityId]);

  // UX helpers
  const resetFilters = () => {
    setCityId("");
    setStationId("");
    setPollutantId("");
    setDateFrom("");
    setDateTo("");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-20 backdrop-blur bg-white/80 border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-600" />
            <div>
              <h1 className="text-xl font-bold">Моніторинг промислових зон України</h1>
              <p className="text-xs text-gray-500 -mt-1">
                Модуль прогнозування екологічних показників на основі ML
              </p>
            </div>
          </div>
          <button
            onClick={resetFilters}
            className="text-sm px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-xl"
          >
            Скинути фільтри
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Filters */}
        <Card>
          <SectionTitle
            title="Фільтри"
            right={<div className="flex items-center gap-2 text-gray-500 text-sm"><Filter className="w-4 h-4"/>Обмежте вибір для точнішого аналізу</div>}
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
            {/* City */}
            <div>
              <label className="block text-sm text-gray-500 mb-1">Місто</label>
              <select
                className="w-full rounded-xl border-gray-200 focus:ring-2 focus:ring-emerald-500"
                value={cityId}
                onChange={(e) => setCityId(e.target.value ? Number(e.target.value) : "")}
              >
                <option value="">Всі міста</option>
                {cities.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Station */}
            <div>
              <label className="block text-sm text-gray-500 mb-1">Станція</label>
              <select
                className="w-full rounded-xl border-gray-200 focus:ring-2 focus:ring-emerald-500"
                value={stationId}
                onChange={(e) => setStationId(e.target.value ? Number(e.target.value) : "")}
                disabled={!cityId}
              >
                <option value="">Всі станції</option>
                {stations.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Pollutant */}
            <div>
              <label className="block text-sm text-gray-500 mb-1">Полютант</label>
              <select
                className="w-full rounded-xl border-gray-200 focus:ring-2 focus:ring-emerald-500"
                value={pollutantId}
                onChange={(e) => setPollutantId(e.target.value ? Number(e.target.value) : "")}
              >
                <option value="">Обрати</option>
                {pollutants.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.code} — {p.description}
                  </option>
                ))}
              </select>
            </div>

            {/* Date from */}
            <div>
              <label className="block text-sm text-gray-500 mb-1">Від дати</label>
              <input
                type="date"
                className="w-full rounded-xl border-gray-200 focus:ring-2 focus:ring-emerald-500"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>

            {/* Date to */}
            <div>
              <label className="block text-sm text-gray-500 mb-1">До дати</label>
              <input
                type="date"
                className="w-full rounded-xl border-gray-200 focus:ring-2 focus:ring-emerald-500"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>

            {/* Status */}
            <div className="flex items-end">
              <div className="text-sm text-gray-500">
                {loading ? (
                  <span className="animate-pulse">Завантаження…</span>
                ) : error ? (
                  <span className="text-red-600">Помилка: {error}</span>
                ) : (
                  <span>
                    {measurements.length ? `Записів: ${measurements.length}` : "Дані відсутні"}
                  </span>
                )}
              </div>
            </div>
          </div>
        </Card>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <Stat
              icon={<Gauge className="w-6 h-6" />}
              label="Середнє значення"
              value={stats?.avg ? Number(stats.avg.toFixed(3)) : null}
              hint={pollutantId ? `для ${pollutants.find(p=>p.id===Number(pollutantId))?.code}` : undefined}
            />
          </Card>
          <Card>
            <Stat icon={<ArrowDown className="w-6 h-6" />} label="Мінімум" value={stats?.min} />
          </Card>
          <Card>
            <Stat icon={<ArrowUp className="w-6 h-6" />} label="Максимум" value={stats?.max} />
          </Card>
        </div>

        {/* Chart */}
        <Card className="h-96">
          <SectionTitle title="Динаміка показників" />
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line type="monotone" dataKey="value" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Table */}
        <Card>
          <SectionTitle title="Таблиця вимірювань" />
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="text-left text-gray-500">
                <tr>
                  <th className="py-2 pr-4">Дата</th>
                  <th className="py-2 pr-4">Місто</th>
                  <th className="py-2 pr-4">Станція</th>
                  <th className="py-2 pr-4">Полютант</th>
                  <th className="py-2 pr-4">Значення</th>
                </tr>
              </thead>
              <tbody>
                {measurements.map((m, i) => (
                  <tr key={`${m.date}-${i}`} className="border-t border-gray-100">
                    <td className="py-2 pr-4 whitespace-nowrap">{m.date}</td>
                    <td className="py-2 pr-4">{m.city}</td>
                    <td className="py-2 pr-4">{m.station}</td>
                    <td className="py-2 pr-4">{m.pollutant}</td>
                    <td className="py-2 pr-4">{m.value}</td>
                  </tr>
                ))}
                {!measurements.length && (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-gray-500">
                      Немає даних для заданих фільтрів
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Map */}
        <Card>
          <SectionTitle title="Карта міст та станцій" />
          <div className="h-[400px] rounded-xl overflow-hidden">
            <MapContainer
              center={selectedCity ? [selectedCity.lat, selectedCity.lng] : [49.0, 31.0]}
              zoom={selectedCity ? 11 : 6}
              scrollWheelZoom={false}
              style={{ height: "100%", width: "100%" }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {cities.map((c) => (
                <Marker key={c.id} position={[c.lat, c.lng]}>
                  <Popup>
                    <div className="text-sm">
                      <div className="font-semibold">{c.name}</div>
                      {cityId === c.id && stations.length > 0 ? (
                        <ul className="mt-1 list-disc list-inside">
                          {stations.map((s) => (
                            <li key={s.id}>{s.name}</li>
                          ))}
                        </ul>
                      ) : (
                        <div className="text-gray-500">Натисніть зверху, щоб обрати місто</div>
                      )}
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        </Card>

        {/* Footer / ML note */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-xs text-gray-500 text-center"
        >
          * Прогнозні значення можуть бути додані як другий графік (наприклад, \"Прогноз\") після інтеграції ML сервісу.
        </motion.div>
      </main>
    </div>
  );
}
