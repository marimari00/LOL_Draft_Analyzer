import React, { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import './HealthDashboard.css';

const DEFAULT_POLL_INTERVAL = 15000; // 15 seconds keeps data fresh without hammering backend
const formatIso = (isoString) => {
  if (!isoString) return '—';
  try {
    const date = new Date(isoString);
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
  } catch (err) {
    return isoString;
  }
};

const formatPercent = (value, digits = 2) => (
  typeof value === 'number' ? `${(value * 100).toFixed(digits)}%` : '—'
);

const formatNumber = (value) => (
  typeof value === 'number' ? value.toLocaleString() : '—'
);

const prettifyCompName = (value = '') => value
  .split('_')
  .map(part => part.charAt(0).toUpperCase() + part.slice(1))
  .join(' ');

const HealthDashboard = ({ apiBase = 'http://localhost:8000', pollIntervalMs = DEFAULT_POLL_INTERVAL }) => {
  const [snapshot, setSnapshot] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${apiBase}/health`);
      setSnapshot(response.data);
      setLastUpdated(new Date());
      setError(null);
      setHistory(prev => {
        const next = [...prev, {
          ts: Date.now(),
          backlog: response.data?.telemetry?.backlog_events ?? null,
          status: response.data?.status || 'unknown'
        }];
        return next.slice(-25); // keep last 25 points
      });
    } catch (err) {
      setError(err.message || 'Failed to load health data');
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  useEffect(() => {
    const interval = setInterval(fetchHealth, pollIntervalMs);
    return () => clearInterval(interval);
  }, [fetchHealth, pollIntervalMs]);

  const modelEntries = useMemo(() => {
    if (!snapshot?.models) return [];
    return Object.entries(snapshot.models).map(([key, value]) => ({
      key,
      value
    }));
  }, [snapshot]);

  const latestTelemetry = snapshot?.telemetry || {};
  const latestCalibration = snapshot?.calibration || {};
  const simulationSummary = useMemo(() => snapshot?.simulation_summary || {}, [snapshot]);

  const simulationReady = simulationSummary?.status === 'ready';
  const simulationMetadata = simulationSummary?.metadata || {};
  const simAnalysis = useMemo(() => simulationSummary?.analysis || {}, [simulationSummary]);
  const predictionDistribution = simAnalysis?.prediction_distribution || {};
  const confidenceMetrics = simAnalysis?.confidence_metrics || {};
  const topMatchups = useMemo(() => (
    Array.isArray(simAnalysis?.top_matchups)
      ? simAnalysis.top_matchups.slice(0, 5)
      : []
  ), [simAnalysis]);
  const bottomMatchups = useMemo(() => (
    Array.isArray(simAnalysis?.bottom_matchups)
      ? simAnalysis.bottom_matchups.slice(0, 5)
      : []
  ), [simAnalysis]);
  const compositionTotals = useMemo(() => (
    Array.isArray(simAnalysis?.composition_totals)
      ? simAnalysis.composition_totals.slice(0, 4)
      : []
  ), [simAnalysis]);

  return (
    <div className="health-dashboard">
      <div className="health-header">
        <div>
          <h2>Backend Health</h2>
          <p className="health-subtitle">Live metrics from FastAPI `/health` endpoint</p>
        </div>
        <div className="health-actions">
          <button type="button" onClick={fetchHealth} disabled={loading}>
            Refresh
          </button>
          <span className="health-updated">Last updated: {lastUpdated ? formatIso(lastUpdated.toISOString()) : '—'}</span>
        </div>
      </div>

      {error && (
        <div className="health-error" role="alert">
          {error}
        </div>
      )}

      <div className="health-grid">
        <section className="health-card">
          <h3>Status</h3>
          <div className={`health-status-pill ${snapshot?.status || 'unknown'}`}>
            {snapshot?.status || 'unknown'}
          </div>
          <dl>
            <div>
              <dt>Version</dt>
              <dd>{snapshot?.version || '—'}</dd>
            </div>
            <div>
              <dt>Generated</dt>
              <dd>{formatIso(snapshot?.generated_at)}</dd>
            </div>
          </dl>
        </section>

        <section className="health-card">
          <h3>Model Artifacts</h3>
          <ul>
            {modelEntries.map(entry => (
              <li key={entry.key}>
                <span className="label">{entry.key.replace(/_/g, ' ')}</span>
                <span className={entry.value ? 'value success' : 'value danger'}>
                  {String(entry.value)}
                </span>
              </li>
            ))}
            {!modelEntries.length && <li>No model data reported.</li>}
          </ul>
        </section>

        <section className="health-card">
          <h3>Telemetry Backlog</h3>
          <dl>
            <div>
              <dt>Events Queued</dt>
              <dd>{latestTelemetry.backlog_events ?? '—'}</dd>
            </div>
            <div>
              <dt>Log Size</dt>
              <dd>{latestTelemetry.size_bytes ? `${(latestTelemetry.size_bytes / 1024).toFixed(1)} KB` : '—'}</dd>
            </div>
            <div>
              <dt>Last Event</dt>
              <dd>{formatIso(latestTelemetry.last_event_ts)}</dd>
            </div>
          </dl>
          <p className="data-path">{latestTelemetry.log_path}</p>
        </section>

        <section className="health-card">
          <h3>Calibration</h3>
          <dl>
            <div>
              <dt>Samples</dt>
              <dd>{latestCalibration.samples ?? '—'}</dd>
            </div>
            <div>
              <dt>ECE</dt>
              <dd>{typeof latestCalibration.ece === 'number' ? latestCalibration.ece.toFixed(4) : '—'}</dd>
            </div>
            <div>
              <dt>Brier</dt>
              <dd>{typeof latestCalibration.brier === 'number' ? latestCalibration.brier.toFixed(4) : '—'}</dd>
            </div>
            <div>
              <dt>Last Report</dt>
              <dd>{formatIso(latestCalibration.last_report_ts)}</dd>
            </div>
          </dl>
          <p className="data-path">{latestCalibration.report_path}</p>
        </section>

        <section className="health-card">
          <h3>Simulation Summary</h3>
          <dl>
            <div>
              <dt>Status</dt>
              <dd>{simulationSummary.status || 'unknown'}</dd>
            </div>
            <div>
              <dt>Last Run</dt>
              <dd>{formatIso(simulationSummary.last_modified)}</dd>
            </div>
            <div>
              <dt>Total Games</dt>
              <dd>{simulationSummary.metadata?.total_games ?? '—'}</dd>
            </div>
            <div>
              <dt>Blue Win Rate</dt>
              <dd>
                {simulationSummary.analysis?.prediction_distribution?.blue_win_rate ?
                  (simulationSummary.analysis.prediction_distribution.blue_win_rate * 100).toFixed(2) + '%' :
                  '—'}
              </dd>
            </div>
          </dl>
          <p className="data-path">{simulationSummary.path}</p>
        </section>
      </div>

      {simulationSummary?.path && (
        <section className="health-card simulation-breakdown">
          <div className="sim-header">
            <div>
              <h3>Mass Simulation</h3>
              <p className="sim-path">{simulationSummary.path}</p>
            </div>
            <div className={`sim-status ${simulationReady ? 'ready' : simulationSummary?.status || 'unknown'}`}>
              {simulationSummary?.status || 'unknown'}
            </div>
          </div>

          <div className="sim-metrics">
            <div className="sim-metric">
              <span>Total Games</span>
              <strong>{formatNumber(simulationMetadata.total_games || simulationMetadata.games)}</strong>
            </div>
            <div className="sim-metric">
              <span>Blue Win Rate</span>
              <strong>{formatPercent(predictionDistribution.blue_win_rate)}</strong>
            </div>
            <div className="sim-metric">
              <span>Avg Confidence</span>
              <strong>{formatPercent(confidenceMetrics.average_confidence)}</strong>
            </div>
            <div className="sim-metric">
              <span>CI Half-Width</span>
              <strong>{formatPercent(
                predictionDistribution.confidence_half_width ?? confidenceMetrics.confidence_half_width,
                2
              )}</strong>
            </div>
            <div className="sim-metric">
              <span>Last Updated</span>
              <strong>{formatIso(simulationSummary.last_modified)}</strong>
            </div>
          </div>

          {(topMatchups.length || bottomMatchups.length) && (
            <div className="sim-matchup-grid">
              {topMatchups.length > 0 && (
                <div className="sim-table">
                  <div className="sim-table-header">Best Matchups</div>
                  <table>
                    <thead>
                      <tr>
                        <th>Archetype Clash</th>
                        <th>Games</th>
                        <th>Blue WR</th>
                        <th>±</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topMatchups.map((matchup) => (
                        <tr key={`top-${matchup.blue_comp}-${matchup.red_comp}`}>
                          <td>{prettifyCompName(matchup.blue_comp)} vs {prettifyCompName(matchup.red_comp)}</td>
                          <td>{formatNumber(matchup.games)}</td>
                          <td>{formatPercent(matchup.avg_blue_win_prob)}</td>
                          <td>{formatPercent(matchup.blue_ci_half_width)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {bottomMatchups.length > 0 && (
                <div className="sim-table">
                  <div className="sim-table-header">Risky Matchups</div>
                  <table>
                    <thead>
                      <tr>
                        <th>Archetype Clash</th>
                        <th>Games</th>
                        <th>Blue WR</th>
                        <th>±</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bottomMatchups.map((matchup) => (
                        <tr key={`bottom-${matchup.blue_comp}-${matchup.red_comp}`}>
                          <td>{prettifyCompName(matchup.blue_comp)} vs {prettifyCompName(matchup.red_comp)}</td>
                          <td>{formatNumber(matchup.games)}</td>
                          <td>{formatPercent(matchup.avg_blue_win_prob)}</td>
                          <td>{formatPercent(matchup.blue_ci_half_width)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {compositionTotals.length > 0 && (
            <div className="sim-compositions">
              {compositionTotals.map(comp => (
                <div key={comp.composition} className="composition-card">
                  <div className="comp-label">{prettifyCompName(comp.composition)}</div>
                  <div className="comp-value">{formatPercent(comp.avg_blue_probability)}</div>
                  <div className="comp-meta">
                    {formatNumber(comp.games)} games • ±{formatPercent(comp.ci_half_width)}
                  </div>
                </div>
              ))}
            </div>
          )}

          {!simulationReady && (
            <p className="sim-warning">Summary file not ready or missing — run the mass simulator or check backend logs.</p>
          )}
        </section>
      )}

      <section className="health-card history-card">
        <h3>Telemetry Trend</h3>
        {history.length ? (
          <div className="history-list">
            {history.map(point => (
              <div key={point.ts} className="history-row">
                <span>{new Date(point.ts).toLocaleTimeString()}</span>
                <span>{point.backlog ?? '—'} events</span>
                <span className={`status-dot ${point.status}`}></span>
              </div>
            ))}
          </div>
        ) : (
          <p>No history yet.</p>
        )}
      </section>
    </div>
  );
};

export default HealthDashboard;
