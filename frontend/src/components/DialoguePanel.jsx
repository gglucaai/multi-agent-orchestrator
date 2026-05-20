import React, { useEffect, useRef } from 'react';
import { MessageCircle } from 'lucide-react';

/**
 * DialoguePanel - Shows back-and-forth conversation between orchestrator and agents
 * This is the centerpiece of the new visualization
 */
export default function DialoguePanel({ messages, agents }) {
  const scrollRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="bg-slate-900/80 border-2 border-indigo-500/30 rounded-lg p-6 text-center">
        <MessageCircle className="w-8 h-8 text-indigo-400 mx-auto mb-2" />
        <p className="font-retro text-lg text-indigo-300">
          Dialogue will appear here when orchestration starts
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/80 border-2 border-indigo-500/30 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-indigo-900/50 border-b-2 border-indigo-500/30 p-3 flex items-center gap-2">
        <MessageCircle className="w-5 h-5 text-indigo-300" />
        <h3 className="font-pixel text-xs text-indigo-300">
          ORCHESTRATOR ↔ AGENTS DIALOGUE
        </h3>
        <span className="ml-auto font-retro text-sm text-slate-400">
          {messages.length} messages
        </span>
      </div>

      {/* Messages */}
      <div 
        ref={scrollRef}
        className="p-4 max-h-[500px] overflow-y-auto space-y-3"
      >
        {messages.map((msg, idx) => (
          <DialogueMessage 
            key={idx} 
            message={msg} 
            agents={agents}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * Individual dialogue message - styled differently for orchestrator vs agent
 */
function DialogueMessage({ message, agents }) {
  const isOrchestrator = message.speaker === 'orchestrator';
  const agent = !isOrchestrator ? agents[message.speaker] : null;
  const targetAgent = isOrchestrator ? agents[message.to] : null;
  
  // Determine if message is approval or rejection
  const isApproval = message.message?.startsWith('✓');
  const isRejection = message.message?.startsWith('✗');

  return (
    <div className={`flex gap-3 ${isOrchestrator ? '' : 'flex-row-reverse'}`}>
      {/* Avatar */}
      <div className="flex-shrink-0">
        {isOrchestrator ? (
          <div className="relative">
            <div className="absolute inset-0 bg-indigo-500 rounded-full blur-md opacity-60" />
            <img
              src="/images/orchestrator.png"
              alt="Orchestrator"
              className="pixel-art w-12 h-12 relative bg-slate-800 rounded-lg p-1 border-2 border-indigo-400"
            />
          </div>
        ) : agent ? (
          <div className="relative">
            <div 
              className="absolute inset-0 rounded-full blur-md opacity-60"
              style={{ backgroundColor: agent.color }}
            />
            <img
              src={`/images/${agent.character}`}
              alt={agent.name}
              className="pixel-art w-12 h-12 relative bg-slate-800 rounded-lg p-1 border-2"
              style={{ borderColor: agent.color }}
            />
          </div>
        ) : null}
      </div>

      {/* Message content */}
      <div className={`flex-1 max-w-[80%] ${isOrchestrator ? '' : 'text-right'}`}>
        {/* Speaker label */}
        <div className={`flex items-center gap-2 mb-1 ${isOrchestrator ? '' : 'justify-end'}`}>
          <span 
            className="font-pixel text-[10px]"
            style={{ color: isOrchestrator ? '#818cf8' : agent?.color }}
          >
            {isOrchestrator 
              ? `ORCHESTRATOR → ${targetAgent?.name?.toUpperCase().replace(' AGENT', '') || ''}` 
              : `${agent?.name?.toUpperCase() || message.speaker.toUpperCase()}`}
          </span>
          {message.round > 0 && (
            <span className="font-retro text-xs text-yellow-400">
              [Round {message.round}]
            </span>
          )}
        </div>

        {/* Message bubble */}
        <div 
          className={`inline-block p-3 rounded-lg font-retro text-base ${
            isOrchestrator 
              ? 'bg-indigo-900/40 border-2 border-indigo-500/50 text-indigo-100' 
              : 'bg-slate-800/80 border-2 text-slate-100'
          } ${
            isApproval ? 'border-green-500/70 bg-green-900/30' : 
            isRejection ? 'border-red-500/70 bg-red-900/30' : ''
          }`}
          style={!isOrchestrator && agent ? { borderColor: `${agent.color}80` } : {}}
        >
          {message.message}
          
          {/* Show data preview if attached */}
          {message.data && (
            <details className="mt-2">
              <summary className="cursor-pointer text-xs text-indigo-300 hover:text-indigo-200">
                ▶ View data (click to expand)
              </summary>
              <pre className="mt-2 p-2 bg-slate-950 rounded text-[11px] text-green-300 overflow-x-auto max-h-32 overflow-y-auto">
                {typeof message.data === 'string' 
                  ? message.data.substring(0, 300) + '...'
                  : JSON.stringify(message.data, null, 2).substring(0, 300) + '...'}
              </pre>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}
