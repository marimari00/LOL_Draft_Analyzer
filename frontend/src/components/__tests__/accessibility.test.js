import React from 'react';
import { render, waitFor } from '@testing-library/react';
import { axe } from 'jest-axe';
import DraftBoard from '../DraftBoard';
import HealthDashboard from '../HealthDashboard';
import axios from 'axios';

jest.mock('axios');

const noop = () => {};

const MOCK_PICK_ORDER = [
  { id: 'B1', team: 'blue', role: 'TOP' },
  { id: 'R1', team: 'red', role: 'TOP' }
];

const axeOptions = {
  rules: {
    // Disable contrast rule because jsdom cannot compute our gradients accurately.
    'color-contrast': { enabled: false }
  }
};

describe('Accessibility smoke tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('DraftBoard renders without obvious accessibility violations', async () => {
    const { container } = render(
      <DraftBoard
        bluePicks={[]}
        redPicks={[]}
        blueBans={[]}
        redBans={[]}
        currentTeam="blue"
        currentAction="pick"
        activeSlotId="B1"
        pickOrder={MOCK_PICK_ORDER}
        teamOrder={['blue', 'red']}
        onMoveLane={noop}
        onResetPickOrder={noop}
        onBanClick={noop}
        availableChampions={[{ name: 'Garen', roles: ['TOP'] }]}
        onInlinePick={noop}
        championLookup={{}}
        playmakerHighlight={null}
      />
    );

    const results = await axe(container, axeOptions);
    expect(results).toHaveNoViolations();
  });

  test('HealthDashboard snapshot is accessible after data loads', async () => {
    const nowIso = new Date().toISOString();
    axios.get.mockResolvedValue({
      data: {
        status: 'online',
        version: '1.1.0',
        generated_at: nowIso,
        models: {
          predictor_loaded: true,
          champion_index_loaded: true
        },
        telemetry: {
          backlog_events: 3,
          size_bytes: 2048,
          last_event_ts: nowIso,
          log_path: '/tmp/prediction_log.jsonl'
        },
        calibration: {
          samples: 240,
          ece: 0.034,
          brier: 0.22,
          last_report_ts: nowIso,
          report_path: '/tmp/calibration_report.json'
        }
      }
    });

    const { container } = render(<HealthDashboard apiBase="http://localhost:8000" pollIntervalMs={60000} />);
    await waitFor(() => expect(axios.get).toHaveBeenCalledTimes(1));

    const results = await axe(container, axeOptions);
    expect(results).toHaveNoViolations();
  });
});
