import React from "react";

export function EventsTimelinePanel({ events }: { events: any }) {
  const list: any[] = Array.isArray(events) ? events : [];
  const tail = list.slice(-50).reverse();

  return (
    <div className="card">
      <div className="card-header">
        <h3 style={{ margin: 0 }}>Events</h3>
      </div>
      <div style={{ fontSize: "12px", maxHeight: "240px", overflow: "auto" }}>
        {tail.length === 0 ? (
          <div style={{ color: "#9fb4cc" }}>Sin eventos.</div>
        ) : (
          <ul style={{ margin: 0, paddingLeft: "18px" }}>
            {tail.map((e, i) => (
              <li key={i}>
                <span style={{ opacity: 0.8 }}>
                  {e?.timestamp || e?.ts || e?.time || ""}
                </span>{" "}
                <span>{e?.type || e?.event_type || e?.level || "event"}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

