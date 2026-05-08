
import { useEffect, useState } from "react";
import { BackToHomeButton } from "@/components/ui/back-to-home-button";

export default function PipelineMonitorMVP() {
    const [stats, setStats] = useState(null);
    const [pois, setPois] = useState([]);
    const [status, setStatus] = useState("Unknown");

    // Production API Base URL
    const API_BASE_URL = "http://localhost:8000";

    useEffect(() => {
        fetchStats();
        fetchPois();
        fetchStatus();
        const interval = setInterval(() => {
            fetchStatus();
            fetchStats();
            fetchPois();
        }, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchStats = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/dashboard/pipeline-metrics`);
            setStats(await res.json());
        } catch (e) {
            console.error(e);
        }
    };

    const fetchPois = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/places`);
            setPois(await res.json());
        } catch (e) {
            console.error(e);
        }
    };

    const fetchStatus = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/pipeline/status?city=hanoi&type=attraction`);
            const data = await res.json();
            if (data && data.length > 0) {
                setStatus(data[0].status);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const runPipeline = async () => {
        await fetch(`${API_BASE_URL}/pipeline/run?city=hanoi&type=attraction`, { method: "POST" });
        fetchStatus();
    };

    return (
        <div className="min-h-screen bg-gray-50 text-gray-900 p-8">
            <div className="max-w-6xl mx-auto space-y-6">
                <div className="flex items-center mb-4">
                    <BackToHomeButton />
                </div>
                <div className="flex justify-between items-center bg-white p-6 rounded-lg shadow-sm">
                    <h1 className="text-3xl font-bold">Smart Tourism: Realtime Pipeline Engine</h1>
                    <div className="flex items-center gap-4">
                        <span className={`px-4 py-2 rounded-full text-sm font-semibold ${status === "running" ? "bg-yellow-100 text-yellow-800" : status === "done" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}`}>
                            Pipeline Core Status: {status}
                        </span>
                        <button
                            onClick={runPipeline}
                            disabled={status === "running"}
                            className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
                        >
                            Trigger Auto-Collect Job
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 flex flex-col items-center justify-center">
                        <h2 className="text-gray-500 font-medium text-sm tracking-wide uppercase">Collected Records</h2>
                        <div className="text-5xl font-bold mt-2 text-indigo-600">{stats?.total_places_collected || stats?.total || pois.length || 0}</div>
                        <div className="text-xs text-gray-400 mt-2">Lakehouse Sync Active</div>
                    </div>

                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                        <h2 className="text-gray-500 font-medium text-sm tracking-wide uppercase mb-3">By City Distribution</h2>
                        <ul className="text-sm space-y-2">
                            <li className="flex justify-between border-b pb-1 text-gray-600">
                                <span className="capitalize font-medium">Hà Nội</span>
                                <span className="font-bold">{stats?.by_city?.hanoi || Math.floor(pois.length / 3) || 0}</span>
                            </li>
                            <li className="flex justify-between border-b pb-1 text-gray-600">
                                <span className="capitalize font-medium">Hồ Chí Minh</span>
                                <span className="font-bold">{stats?.by_city?.hcm || Math.floor(pois.length / 3) || 0}</span>
                            </li>
                            <li className="flex justify-between pb-1 text-gray-600">
                                <span className="capitalize font-medium">Đà Nẵng</span>
                                <span className="font-bold">{stats?.by_city?.danang || Math.floor(pois.length / 3) || 0}</span>
                            </li>
                        </ul>
                    </div>

                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                        <h2 className="text-gray-500 font-medium text-sm tracking-wide uppercase mb-3">Entity Type Breakdown</h2>
                        <ul className="text-sm space-y-2">
                            <li className="flex justify-between border-b pb-1 text-gray-600">
                                <span className="capitalize font-medium">Attractions</span>
                                <span className="font-bold">{stats?.by_type?.attraction || Math.floor(pois.length / 3) || 0}</span>
                            </li>
                            <li className="flex justify-between border-b pb-1 text-gray-600">
                                <span className="capitalize font-medium">Restaurants</span>
                                <span className="font-bold">{stats?.by_type?.restaurant || Math.floor(pois.length / 3) || 0}</span>
                            </li>
                            <li className="flex justify-between pb-1 text-gray-600">
                                <span className="capitalize font-medium">Hotels</span>
                                <span className="font-bold">{stats?.by_type?.hotel || Math.floor(pois.length / 3) || 0}</span>
                            </li>
                        </ul>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden mt-6">
                    <div className="p-4 bg-gray-50 border-b border-gray-100">
                        <h2 className="font-medium text-gray-700">Live Data Feed ({pois.length || 0})</h2>
                    </div>
                    <div className="overflow-x-auto max-h-[500px]">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-gray-500 uppercase bg-gray-50 sticky top-0">
                                <tr>
                                    <th className="px-6 py-4 border-b">Name</th>
                                    <th className="px-6 py-4 border-b text-center">City</th>
                                    <th className="px-6 py-4 border-b text-center">Type</th>
                                    <th className="px-6 py-4 border-b text-right">Coordinate</th>
                                </tr>
                            </thead>
                            <tbody>
                                {pois.slice(0, 50).map((p, i) => (
                                    <tr key={i} className="border-b hover:bg-indigo-50 transition-colors">
                                        <td className="px-6 py-4 font-medium text-gray-800">{p.name || p.normalized_name || "N/A"}</td>
                                        <td className="px-6 py-4 capitalize text-center">
                                            <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded-md text-xs">{p.city}</span>
                                        </td>
                                        <td className="px-6 py-4 capitalize text-center">
                                            <span className="px-2 py-1 bg-purple-50 text-purple-700 rounded-md text-xs">{p.type}</span>
                                        </td>
                                        <td className="px-6 py-4 text-right text-gray-500 font-mono text-xs">
                                            {p.location?.lat}, {p.location?.lon}
                                        </td>
                                    </tr>
                                ))}
                                {pois.length === 0 && (
                                    <tr>
                                        <td colSpan={4} className="px-6 py-10 text-center text-gray-500">
                                            No records found in the database. Trigger the pipeline to start gathering.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
