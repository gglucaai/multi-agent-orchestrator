import React, { useEffect, useRef, useState } from 'react';
import { Eye } from 'lucide-react';

/**
 * OrchestratorNode - The central conductor
 * - Wobbles each time an agent bumps into it (bumpKey changes)
 * - Shows reviewing state when critiquing agent work
 */
export default function OrchestratorNode({ isActive, isReviewing, message, progress, bumpKey = 0 }) {
  const [bumping, setBumping] = useState(false);
  const lastBumpRef = useRef(0);

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

  return (
    <div className="flex flex-col items-center">
      {/* Orchestrator Character with extra glow */}
      <div className={`relative ${isActive ? 'orchestrator-active' : ''} ${bumping ? 'orchestrator-bump' : ''}`}>
        <div className="absolute inset-0 rounded-full bg-indigo-500/20 blur-3xl scale-150 -z-10" />
        <div className="absolute inset-0 rounded-full bg-purple-500/20 blur-2xl scale-125 -z-10" />

        {/* Crown/Halo effect */}
        {isActive && (
          <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 z-20">
            <div className="font-pixel text-[8px] text-yellow-300 animate-pulse">
              ★ ORCHESTRATOR ★
            </div>
          </div>
        )}

        {/* Reviewing indicator */}
        {isReviewing && (
          <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 z-20">
            <div className="bg-yellow-500 px-2 py-1 rounded font-pixel text-[9px] text-white flex items-center gap-1 animate-pulse">
              <Eye className="w-3 h-3" />
              REVIEWING
            </div>
          </div>
        )}

        {/* Character container */}
        <div className={`relative bg-gradient-to-br from-indigo-900 to-purple-900 rounded-xl p-4 border-4 shadow-2xl transition-colors ${
          isReviewing ? 'border-yellow-400' : 'border-indigo-400'
        }`}>
          <img
            src="/images/orchestrator.png"
            alt="Orchestrator"
            className="pixel-art w-32 h-32 md:w-36 md:h-36"
          />

          {isActive && (
            <div className="absolute -bottom-2 -right-2 bg-yellow-400 rounded-full w-6 h-6 flex items-center justify-center animate-bounce">
              <span className="text-xs">⚡</span>
            </div>
          )}

          {/* Shockwave ring on bump */}
          {bumping && <div className="orchestrator-shockwave" />}
        </div>
      </div>

      {/* Label */}
      <div className="mt-3 text-center max-w-[200px]">
        <div className="font-pixel text-xs text-indigo-300 px-3 py-2 bg-slate-900/80 rounded border-2 border-indigo-400">
          ORCHESTRATOR
        </div>

        <div className="mt-2 font-retro text-sm text-white bg-slate-900/90 px-3 py-2 rounded border border-indigo-500/50 min-h-[40px] flex items-center justify-center">
          {message}
        </div>

        <div className="mt-2 bg-slate-800 rounded-full h-2 overflow-hidden border border-indigo-500/30">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="font-retro text-xs text-indigo-300 mt-1">
          {Math.round(progress)}% Complete
        </div>
      </div>
    </div>
  );
}
