type Props = {
  stations: { id: number; name: string }[];
  onSelect: (id: number) => void;
};

export default function StationSelector({ stations, onSelect }: Props) {
  return (
    <select
      className="border rounded-xl p-2 w-full"
      onChange={(e) => onSelect(Number(e.target.value))}
      defaultValue=""
    >
      <option value="" disabled>
        Оберіть станцію
      </option>
      {stations.map((s) => (
        <option key={s.id} value={s.id}>
          {s.name}
        </option>
      ))}
    </select>
  );
}

