import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { DeviceInformationCard } from '../components/investigation/DeviceInformationCard';

describe('DeviceInformationCard Component', () => {
  it('renders new device with warning badge and client telemetry', () => {
    const device = {
      device_id: 'device-x-999',
      browser: 'Chrome 128',
      operating_system: 'Windows 11',
      ip_address: '103.21.144.12',
      is_new: true,
      is_trusted: false,
      first_seen_at: '2026-09-30T10:21:00Z',
      last_seen_at: '2026-09-30T10:21:00Z',
    };

    render(<DeviceInformationCard device={device} />);

    expect(screen.getByText('NEW DEVICE ⚠️')).toBeInTheDocument();
    expect(screen.getByText('device-x-999')).toBeInTheDocument();
    expect(screen.getByText('Chrome 128')).toBeInTheDocument();
    expect(screen.getByText('Windows 11')).toBeInTheDocument();
    expect(screen.getByText('103.21.144.12')).toBeInTheDocument();
  });

  it('renders known device badge when is_new is false', () => {
    const device = {
      device_id: 'device-trusted-1',
      browser: 'Firefox',
      operating_system: 'macOS',
      is_new: false,
      is_trusted: true,
    };

    render(<DeviceInformationCard device={device} />);
    expect(screen.getByText('KNOWN DEVICE')).toBeInTheDocument();
    expect(screen.getByText('Verified by User')).toBeInTheDocument();
  });
});
