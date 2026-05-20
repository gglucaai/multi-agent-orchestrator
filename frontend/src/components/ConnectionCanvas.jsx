import React from 'react';

/**
 * ConnectionCanvas - SVG lines connecting orchestrator to each agent
 * Lines stretch/compress as agents physically move toward the orchestrator.
 */

const AGENT_POSITIONS = {
  ideation: { angle: -90 },
  market_research: { angle: -30 },
  validation: { angle: 30 },
  refinement: { angle: 90 },
  business_model: { angle: 150 },
  report_writer: { angle: 210 }
};

export default function ConnectionCanvas({
  agents,
  agentStatuses,
  activeAgent,
  dataPackets,
  getAgentPosition,
  engagedRadius = 150,
  restRadius = 280
}) {
  // SVG viewbox center
  const centerX = 0;
  const centerY = 0;

  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ overflow: 'visible' }}
    >
      <defs>
        {/* Gradient for connection lines */}
        <linearGradient id="connectionGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#6366f1" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#818cf8" stopOpacity="0.3" />
        </linearGradient>

        <linearGradient id="activeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#fbbf24" stopOpacity="1" />
          <stop offset="100%" stopColor="#f59e0b" stopOpacity="1" />
        </linearGradient>

        <linearGradient id="completeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#10b981" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#34d399" stopOpacity="0.5" />
        </linearGradient>

        {/* Glow filter */}
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>

        {/* Strong glow for active connections */}
        <filter id="strongGlow">
          <feGaussianBlur stdDeviation="6" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      {/* Lines from orchestrator (center) to each agent */}
      <g transform="translate(50%, 50%)">
        {Object.keys(AGENT_POSITIONS).map((key) => {
          const position = AGENT_POSITIONS[key];
          const isActive = activeAgent === key;
          const radius = isActive ? engagedRadius : restRadius;
          const coords = getAgentPosition(position.angle, radius);
          const status = agentStatuses[key];

          // Determine line style based on status
          let stroke = "url(#connectionGradient)";
          let strokeWidth = "2";
          let strokeDasharray = "4 4";
          let opacity = 0.4;
          let filter = "";

          if (isActive) {
            stroke = "url(#activeGradient)";
            strokeWidth = "4";
            strokeDasharray = "0";
            opacity = 1;
            filter = "url(#strongGlow)";
          } else if (status === 'complete') {
            stroke = "url(#completeGradient)";
            strokeWidth = "2";
            strokeDasharray = "0";
            opacity = 0.7;
            filter = "url(#glow)";
          }

          return (
            <g key={key}>
              {/* Connection line */}
              <line
                x1={centerX}
                y1={centerY}
                x2={coords.x}
                y2={coords.y}
                stroke={stroke}
                strokeWidth={strokeWidth}
                strokeDasharray={strokeDasharray}
                opacity={opacity}
                filter={filter}
                className={isActive ? 'connection-line connection-line-active' : 'connection-line-static'}
              />

              {/* Animated data packets traveling along line */}
              {dataPackets
                .filter(p => p.agentKey === key)
                .map(packet => (
                  <g key={packet.id}>
                    <DataPacket
                      from={packet.direction === 'out' ? { x: centerX, y: centerY } : coords}
                      to={packet.direction === 'out' ? coords : { x: centerX, y: centerY }}
                      color={packet.direction === 'out' ? '#fbbf24' : '#10b981'}
                    />
                  </g>
                ))}
            </g>
          );
        })}
      </g>
    </svg>
  );
}

/**
 * Animated data packet that travels along a connection line
 */
function DataPacket({ from, to, color }) {
  return (
    <>
      {/* Outer glow */}
      <circle r="10" fill={color} opacity="0.3" filter="url(#strongGlow)">
        <animate
          attributeName="cx"
          from={from.x}
          to={to.x}
          dur="1.5s"
          fill="freeze"
        />
        <animate
          attributeName="cy"
          from={from.y}
          to={to.y}
          dur="1.5s"
          fill="freeze"
        />
      </circle>

      {/* Inner bright dot */}
      <circle r="5" fill={color}>
        <animate
          attributeName="cx"
          from={from.x}
          to={to.x}
          dur="1.5s"
          fill="freeze"
        />
        <animate
          attributeName="cy"
          from={from.y}
          to={to.y}
          dur="1.5s"
          fill="freeze"
        />
        <animate
          attributeName="r"
          values="3;6;3"
          dur="0.5s"
          repeatCount="3"
        />
      </circle>

      {/* Trail effect */}
      <circle r="3" fill={color} opacity="0.6">
        <animate
          attributeName="cx"
          from={from.x}
          to={to.x}
          dur="1.5s"
          begin="0.2s"
          fill="freeze"
        />
        <animate
          attributeName="cy"
          from={from.y}
          to={to.y}
          dur="1.5s"
          begin="0.2s"
          fill="freeze"
        />
      </circle>
    </>
  );
}
