import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

type Measurement = {
  date: string;
  value: number;
};

export default function ChartView({ data }: { data: Measurement[] }) {
  const chartData = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString("uk-UA", {
      day: "2-digit",
      month: "2-digit",
    }),
    value: d.value,
  }));

  console.log("ChartData:", chartData);

  return (
    <div className="bg-white shadow rounded-2xl p-4">
      <div style={{ width: "100%", height: 350 }}>
        <ResponsiveContainer>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis domain={[0, "dataMax"]} />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#2563eb"
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
