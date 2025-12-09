import React from "react";

export function ShubPanel() {
  return (
    <div className="card">
      <div className="card-header">
        <h2>Shub Dashboard</h2>
      </div>
      <p>Monitor Shub sessions and audio analysis. Upload via backend /shub/upload.</p>
      <ul>
        <li>Sessions: live stream via Tentáculo Link.</li>
        <li>Recommendations: coming soon.</li>
      </ul>
    </div>
  );
}
