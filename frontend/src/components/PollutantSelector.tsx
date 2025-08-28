type Props = {
  pollutants: { id: number; code: string; description?: string }[];
  onSelect: (id: number) => void;
};

export default function PollutantSelector({ pollutants, onSelect }: Props) {
  return (
    <select
      className="border rounded-xl p-2 w-full"
      onChange={(e) => onSelect(Number(e.target.value))}
      defaultValue=""
    >
      <option value="" disabled>
        Оберіть полютант
      </option>
      {pollutants.map((p) => (
        <option key={p.id} value={p.id}>
          {p.code} {p.description ? `- ${p.description}` : ""}
        </option>
      ))}
    </select>
  );
}

