import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

export async function getCities() {
  return (await api.get("/cities/")).data;
}

export async function getStations(cityId: number) {
  return (await api.get(`/cities/${cityId}/stations/`)).data;
}

export async function getPollutants() {
  return (await api.get("/pollutants/")).data;
}

export async function getMeasurements(params: {
  cityId?: number;
  stationId?: number;
  pollutantId?: number;
  dateFrom?: string;
  dateTo?: string;
}) {
  return (
    await api.get("/measurements/", {
      params: {
        city_id: params.cityId,
        station_id: params.stationId,
        pollutant_id: params.pollutantId,
        date_from: params.dateFrom,
        date_to: params.dateTo,
      },
    })
  ).data;
}

