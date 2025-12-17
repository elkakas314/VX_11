import * as React from "react";
import { fetchJSON } from "../services/api";

export function MadrePanel() {
    const [plans, setPlans] = React.useState<any[]>([]);
    const [loading, setLoading] = React.useState(true);
    const [expandedId, setExpandedId] = React.useState<string | null>(null);

    React.useEffect(() => {
        const fetch = async () => {
            try {
                const data = await fetchJSON("/operator/madre/plans");
                setPlans(data.plans || data || []);
            } catch (e) {
                console.error("Error fetching plans:", e);
            } finally {
                setLoading(false);
            }
        };
        fetch();
        const interval = setInterval(fetch, 5000);
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="card"><h3>Planes (Madre)</h3><p>Cargando...</p></div>;

    return (
        <div className="card">
            <h3>Planes (Madre Orchestration)</h3>
            {plans.length === 0 ? (
                <p>Sin planes activos</p>
            ) : (
                <table style={{ width: "100%", fontSize: "12px" }}>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Estado</th>
                            <th>Modelo</th>
                            <th>Acción</th>
                        </tr>
                    </thead>
                    <tbody>
                        {plans.slice(0, 10).map((plan) => (
                            <tr key={plan.plan_id || plan.id}>
                                <td>{(plan.plan_id || plan.id || "?").slice(0, 6)}...</td>
                                <td>{plan.status || plan.state || "?"}</td>
                                <td>{plan.feedback?.model || plan.model || "—"}</td>
                                <td>
                                    <button
                                        onClick={() => setExpandedId(expandedId === plan.plan_id ? null : plan.plan_id)}
                                        style={{ fontSize: "10px", padding: "2px 5px" }}
                                    >
                                        {expandedId === plan.plan_id ? "Colapsar" : "Ver"}
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
            {expandedId && (
                <div style={{ marginTop: "10px", padding: "5px", background: "#f0f0f0", borderRadius: "3px" }}>
                    <pre style={{ fontSize: "10px", overflow: "auto", maxHeight: "200px" }}>
                        {JSON.stringify(plans.find(p => p.plan_id === expandedId), null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
}
