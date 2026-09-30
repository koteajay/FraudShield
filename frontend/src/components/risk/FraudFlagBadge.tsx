import React from 'react';
import {
  Zap,
  DollarSign,
  Compass,
  Smartphone,
  Clock,
  KeyRound,
  Store,
  Globe2,
  ShieldAlert,
} from 'lucide-react';

interface RuleVisualConfig {
  displayName: string;
  icon: React.ReactNode;
  classes: string;
}

const KNOWN_RULES_MAP: Record<string, RuleVisualConfig> = {
  // Velocity
  velocity: {
    displayName: 'HIGH VELOCITY',
    icon: <Zap className="shrink-0" />,
    classes: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  },
  'transaction velocity': {
    displayName: 'TRANSACTION VELOCITY',
    icon: <Zap className="shrink-0" />,
    classes: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  },
  // Amount
  amount: {
    displayName: 'UNUSUAL AMOUNT',
    icon: <DollarSign className="shrink-0" />,
    classes: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  },
  'unusual amount': {
    displayName: 'UNUSUAL AMOUNT',
    icon: <DollarSign className="shrink-0" />,
    classes: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  },
  'unusual transaction amount': {
    displayName: 'UNUSUAL AMOUNT',
    icon: <DollarSign className="shrink-0" />,
    classes: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  },
  // Location
  location: {
    displayName: 'IMPOSSIBLE LOCATION',
    icon: <Compass className="shrink-0" />,
    classes: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
  },
  'impossible location': {
    displayName: 'IMPOSSIBLE LOCATION',
    icon: <Compass className="shrink-0" />,
    classes: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
  },
  'impossible travel': {
    displayName: 'IMPOSSIBLE TRAVEL',
    icon: <Compass className="shrink-0" />,
    classes: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
  },
  // Device
  device: {
    displayName: 'DEVICE CHANGE',
    icon: <Smartphone className="shrink-0" />,
    classes: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
  },
  'device change': {
    displayName: 'DEVICE CHANGE',
    icon: <Smartphone className="shrink-0" />,
    classes: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
  },
  // Time
  time: {
    displayName: 'UNUSUAL TIME',
    icon: <Clock className="shrink-0" />,
    classes: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
  },
  'unusual time': {
    displayName: 'UNUSUAL TIME',
    icon: <Clock className="shrink-0" />,
    classes: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
  },
  // Failed logins
  'failed login': {
    displayName: 'FAILED LOGINS',
    icon: <KeyRound className="shrink-0" />,
    classes: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  },
  'multiple failed login': {
    displayName: 'FAILED LOGINS',
    icon: <KeyRound className="shrink-0" />,
    classes: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  },
  // Merchant
  merchant: {
    displayName: 'UNUSUAL MERCHANT',
    icon: <Store className="shrink-0" />,
    classes: 'bg-orange-500/15 text-orange-300 border-orange-500/30',
  },
  'unusual merchant': {
    displayName: 'UNUSUAL MERCHANT',
    icon: <Store className="shrink-0" />,
    classes: 'bg-orange-500/15 text-orange-300 border-orange-500/30',
  },
  // Country
  country: {
    displayName: 'BLACKLISTED GEO',
    icon: <Globe2 className="shrink-0" />,
    classes: 'bg-red-500/15 text-red-300 border-red-500/30',
  },
  'blacklisted country': {
    displayName: 'BLACKLISTED COUNTRY',
    icon: <Globe2 className="shrink-0" />,
    classes: 'bg-red-500/15 text-red-300 border-red-500/30',
  },
};

export interface FraudFlagBadgeProps {
  rule: string;
  scoreImpact?: number;
  size?: 'sm' | 'md';
  showIcon?: boolean;
  className?: string;
}

export const FraudFlagBadge: React.FC<FraudFlagBadgeProps> = ({
  rule,
  scoreImpact,
  size = 'md',
  showIcon = true,
  className = '',
}) => {
  const normalizedKey = rule.trim().toLowerCase();

  // Find exact or partial match in configuration map
  let matchedConfig: RuleVisualConfig | undefined = KNOWN_RULES_MAP[normalizedKey];

  if (!matchedConfig) {
    for (const [key, cfg] of Object.entries(KNOWN_RULES_MAP)) {
      if (normalizedKey.includes(key)) {
        matchedConfig = cfg;
        break;
      }
    }
  }

  const finalConfig: RuleVisualConfig = matchedConfig || {
    displayName: rule.toUpperCase(),
    icon: <ShieldAlert className="shrink-0" />,
    classes: 'bg-slate-800 text-slate-300 border-slate-700',
  };

  const sizeClasses = {
    sm: 'text-[10px] px-2 py-0.5 gap-1 [&>svg]:w-3 [&>svg]:h-3',
    md: 'text-xs px-2.5 py-1 gap-1.5 [&>svg]:w-3.5 [&>svg]:h-3.5',
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-lg border font-mono font-medium ${finalConfig.classes} ${sizeClasses} ${className}`}
      title={rule}
    >
      {showIcon && finalConfig.icon}
      <span>{finalConfig.displayName}</span>
      {scoreImpact !== undefined && (
        <span className="font-semibold text-rose-400 ml-1">+{scoreImpact}</span>
      )}
    </span>
  );
};

export default FraudFlagBadge;
