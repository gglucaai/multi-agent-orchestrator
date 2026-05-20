import React from 'react';
import { X } from 'lucide-react';

/**
 * AgentOutput - Modal showing agent's output when clicked
 */
export default function AgentOutput({ agentKey, agent, output, onClose }) {
  return (
    <div 
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div 
        className="bg-slate-900 border-4 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col shadow-2xl"
        style={{ borderColor: agent.color }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div 
          className="flex items-center justify-between p-4 border-b-2"
          style={{ 
            borderColor: agent.color,
            backgroundColor: `${agent.color}20`
          }}
        >
          <div className="flex items-center gap-3">
            <img
              src={`/images/${agent.character}`}
              alt={agent.name}
              className="pixel-art w-12 h-12"
            />
            <div>
              <h2 
                className="font-pixel text-sm"
                style={{ color: agent.color }}
              >
                {agent.name.toUpperCase()}
              </h2>
              <p className="font-retro text-base text-slate-300">
                {agent.description}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:text-red-400 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        
        {/* Output Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="font-pixel text-xs text-indigo-300 mb-3">
            ▶ AGENT OUTPUT:
          </div>
          <pre className="bg-slate-950 p-4 rounded border border-indigo-500/30 text-green-300 font-mono text-sm whitespace-pre-wrap overflow-x-auto">
            {typeof output === 'string' 
              ? output 
              : JSON.stringify(output, null, 2)}
          </pre>
        </div>
        
        {/* Footer */}
        <div className="p-4 border-t border-indigo-500/30 bg-slate-950">
          <p className="font-retro text-sm text-slate-400 text-center">
            Click outside to close • This output was passed to the next agent
          </p>
        </div>
      </div>
    </div>
  );
}
