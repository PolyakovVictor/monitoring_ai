import React, { useState } from "react";
import { X } from "lucide-react";

const API_BASE = (window as any).ENV_API_BASE || "/api";

type City = {
    id: number;
    name: string;
};

type Props = {
    cities: City[];
    token: string;
    onClose: () => void;
    onSuccess: () => void;
};

export default function AddStationModal({ cities, token, onClose, onSuccess }: Props) {
    const [name, setName] = useState("");
    const [cityId, setCityId] = useState(cities[0]?.id || "");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const res = await fetch(`${API_BASE}/stations/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ name, city_id: Number(cityId) }),
            });

            if (!res.ok) {
                throw new Error("Failed to create station");
            }

            onSuccess();
            onClose();
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white dark:bg-darkCard w-full max-w-md rounded-2xl shadow-2xl border border-gray-100 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold">Add New Station</h2>
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-xl">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Station Name</label>
                        <input
                            type="text"
                            required
                            className="w-full px-4 py-2 rounded-xl border border-gray-200 dark:border-gray-600 focus:ring-2 focus:ring-emerald-500 bg-white dark:bg-darkCard"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="e.g. Central Park Sensor"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">City</label>
                        <select
                            className="w-full px-4 py-2 rounded-xl border border-gray-200 dark:border-gray-600 focus:ring-2 focus:ring-emerald-500 bg-white dark:bg-darkCard"
                            value={cityId}
                            onChange={(e) => setCityId(Number(e.target.value))}
                        >
                            {cities.map((c) => (
                                <option key={c.id} value={c.id}>
                                    {c.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="flex justify-end gap-3 mt-6">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-xl font-medium"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium disabled:opacity-50"
                        >
                            {loading ? "Creating..." : "Create Station"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
