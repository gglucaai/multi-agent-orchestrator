import React, { useEffect, useRef, useState } from 'react';
import { Clock, CheckCircle, RotateCw } from 'lucide-react';

/**
 * AgentNode - Visual representation of an AI agent
 * - Idle bobbing when not active
 * - Bump/collision animation when interacting with the orchestrator
 * - Engaged state when currently working with the orchestrator
 */
export default function AgentNode({
  agentKey,
  agent,
  status,
  isActive,
  hasOutput,
  onClick,
  isSelected,
  revisionCount = 0,
  isEngaged = false,
  bumpKey = 0,
  bumpAngle = 0
}) {
  const [bumping, setBumping] = useState(false);
  const lastBumpRef = useRef(0);

  // Trigger a one-shot bump animation each time bumpKey changes
  useEffect(() => {
    if (!bumpKey || bumpKey === lastBumpRef.current) return;
    lastBumpRef.current = bumpKey;
    setBumping(false);
    const id = requestAnimationFrame(() => setBumping(true));
    const timer = setTimeout(() => setBumping(false), 500);
    return () => {
      cancelAnimationFrame(id);
      clearTimeout(timer);
    };
  }, [bumpKey]);

  const getStatusClass = () => {
    if (isActive) return 'agent-active';
    if (status === 'complete') return 'agent-complete';
    if (status === 'pending') return 'agent-pending';
    return '';
  };

  const getStatusBadge = () => {
    if (status === 'running') {
      return (
        <div className="absolute -top-2 -right-2 bg-yellow-500 rounded-full p-1 status-running z-10">
          <Clock className="w-4 h-4 text-white" />
        </div>
      );
    }
    if (status === 'complete') {
      return (
        <div className="absolute -top-2 -right-2 bg-green-500 rounded-full p-1 z-10">
          <CheckCircle className="w-4 h-4 text-white" />
        </div>
      );
    }
    return null;
  };

  // Direction vector (toward orchestrator) for the bump punch
  const rad = (bumpAngle * Math.PI) / 180;
  const bumpVecX = -Math.cos(rad);
  const bumpVecY = -Math.sin(rad);

  // Inactive agents do a slow vertical bob to feel alive
  const idleClass = !isActive && status !== 'complete' ? 'agent-idle' : '';

  return (
    <div
      className="flex flex-col items-center cursor-pointer"
      onClick={hasOutput ? onClick : undefined}
      style={{ color: agent.color }}
    >
      {/* Character Container */}
      <div
        className={`relative ${getStatusClass()} ${bumping ? '' : idleClass} ${bumping ? 'agent-bump' : ''}`}
        style={{
          '--bump-x': `${bumpVecX * 22}px`,
          '--bump-y': `${bumpVecY * 22}px`
        }}
      >
        {/* Glow effect background */}
        {(isActive || isSelected || isEngaged) && (
          <div
            className="absolute inset-0 rounded-full blur-2xl opacity-60 -z-10"
            style={{
              backgroundColor: agent.color,
              transform: 'scale(1.6)'
            }}
          />
        )}

        {/* Pixel Art Character */}
        <div
          className="relative bg-slate-900/80 rounded-lg p-2 border-2 transition-transform"
          style={{ borderColor: agent.color }}
        >
          <img
            src={`/images/${agent.character}`}
            alt={agent.name}
            className="pixel-art w-20 h-20 md:w-24 md:h-24"
          />
          {getStatusBadge()}

          {/* Revision count badge */}
          {revisionCount > 0 && (
            <div className="absolute -top-2 -left-2 bg-orange-500 rounded-full px-2 py-0.5 flex items-center gap-1 border-2 border-orange-300 z-10">
              <RotateCw className="w-3 h-3 text-white" />
              <span className="font-pixel text-[10px] text-white">
                R{revisionCount}
              </span>
            </div>
          )}

          {/* Speech indicator while engaged */}
          {isEngaged && (
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 -translate-y-full whitespace-nowrap">
              <div className="font-pixel text-[8px] px-2 py-1 rounded bg-slate-900/90 border animate-pulse"
                   style={{ borderColor: agent.color, color: agent.color }}>
                ● LIVE
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Agent Name */}
      <div className="mt-2 text-center">
        <div
          className="font-pixel text-[10px] px-2 py-1 rounded"
          style={{
            color: agent.color,
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            border: `1px solid ${agent.color}40`
          }}
        >
          {agent.name.toUpperCase().replace(' AGENT', '')}
        </div>

        {/* Status text */}
        <div className="font-retro text-xs mt-1 text-slate-400">
          {status === 'pending' && '◌ Standby'}
          {status === 'running' && '⚡ Working...'}
          {status === 'complete' && '✓ Done'}
        </div>

        {/* Click hint */}
        {hasOutput && (
          <div className="font-retro text-[10px] mt-1 text-indigo-300 animate-pulse">
            Click to view
          </div>
        )}
      </div>
    </div>
  );
}
