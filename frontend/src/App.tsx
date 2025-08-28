import { useState, useEffect } from "react";
import { getCities, getStations, getPollutants, getMeasurements } from "./api";
import CitySelector from "./components/CitySelector";
import StationSelector from "./components/StationSelector";
import PollutantSelector from "./components/PollutantSelector";
import ChartView from "./components/ChartView";

function App() {
  const [cities, setCities] = useState<any[]>([]);
  const [stations, setStations] = useState<any[]>([]);
  const [pollutants, setPollutants] = useState<any[]>([]);
  const [data, setData] = useState<any[]>([]);

  const [cityId, setCityId] = useState<number | undefined>(undefined);
  const [stationId, setStationId] = useState<number | undefined>(undefined);
  const [pollutantId, setPollutantId] = useState<number | undefined>(undefined);

  useEffect(() => {
    getCities().then(setCities);
    getPollutants().then(setPollutants);
  }, []);

  useEffect(() => {
    if (cityId) getStations(cityId).then(setStations);
  }, [cityId]);

  useEffect(() => {
    if (pollutantId) {
      getMeasurements({ cityId, stationId, pollutantId }).then(setData);
    }
  }, [cityId, stationId, pollutantId]);

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Моніторинг промислових зон</h1>
      <div className="grid grid-cols-3 gap-4 mb-6">
        <CitySelector cities={cities} onSelect={setCityId} />
        <StationSelector stations={stations} onSelect={setStationId} />
        <PollutantSelector pollutants={pollutants} onSelect={setPollutantId} />
      </div>
      <ChartView data={data} />
    </div>
  );
}

export default App;

