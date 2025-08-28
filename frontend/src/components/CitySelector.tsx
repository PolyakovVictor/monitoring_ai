type Props = {
  cities: { id: number; name: string }[];
  onSelect: (id: number) => void;
};

export default function CitySelector({ cities, onSelect }: Props) {
  return (
    <select
      className="border rounded-xl p-2 w-full"
      onChange={(e) => onSelect(Number(e.target.value))}
      defaultValue=""
    >
      <option value="" disabled>
        Оберіть місто
      </option>
      {cities.map((c) => (
        <option key={c.id} value={c.id}>
          {c.name}
        </option>
      ))}
    </select>
  );
}

