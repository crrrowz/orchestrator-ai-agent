import React from 'react';
import { Coins, Flame, Activity, Zap, DollarSign } from 'lucide-react';

export default function LiveTokenGauge({ tokensUsed = 0, maxBudget = 250000, isRunning = false, lang }) {
  const percentage = Math.min(100, Math.round((tokensUsed / (maxBudget || 1)) * 100));
  const estimatedCostUSD = ((tokensUsed / 1000000) * 3.0).toFixed(4);
  const velocity = isRunning ? Math.floor(Math.random() * 45) + 35 : 0; // simulated tps

  // Circular gauge calculations
  const radius = 32;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="bg-[#0f1523] border border-[#1e273a] rounded-xl p-3.5 flex items-center justify-between shadow-xl">
      {/* Left: Stats & Cost */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-1.5 text-xs font-bold text-white">
          <Coins className="w-4 h-4 text-amber-400" />
          <span>{lang === 'ar' ? 'استهلاك التوكنز والميزانية' : 'Token Velocity & Budget'}</span>
        </div>

        <div className="flex items-baseline gap-1.5 font-mono">
          <span className="text-lg font-extrabold text-amber-300">
            {tokensUsed.toLocaleString()}
          </span>
          <span className="text-[10px] text-gray-500">
            / {maxBudget.toLocaleString()} max
          </span>
        </div>

        <div className="flex items-center gap-3 text-[10px] text-gray-400 font-mono mt-0.5">
          <span className="flex items-center gap-1 text-emerald-400">
            <DollarSign className="w-3 h-3" />
            <span>${estimatedCostUSD}</span>
          </span>
          <span className="flex items-center gap-1 text-cyan-400">
            <Zap className="w-3 h-3" />
            <span>{velocity} tps</span>
          </span>
        </div>
      </div>

      {/* Right: Circular Gauge */}
      <div className="relative flex items-center justify-center">
        <svg className="w-18 h-18 transform -rotate-90" viewBox="0 0 80 80">
          {/* Background circle */}
          <circle
            cx="40"
            cy="40"
            r={radius}
            stroke="#1a2333"
            strokeWidth="6"
            fill="transparent"
          />
          {/* Progress circle */}
          <circle
            cx="40"
            cy="40"
            r={radius}
            stroke="url(#tokenGradient)"
            strokeWidth="6"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-500 ease-out"
          />
          <defs>
            <linearGradient id="tokenGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#06b6d4" />
              <stop offset="100%" stopColor="#10b981" />
            </linearGradient>
          </defs>
        </svg>

        <div className="absolute inset-0 flex flex-col items-center justify-center font-mono">
          <span className="text-xs font-extrabold text-white">{percentage}%</span>
          <span className="text-[8px] text-gray-500 uppercase">Used</span>
        </div>
      </div>
    </div>
  );
}
