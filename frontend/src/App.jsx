import React, { useState, useEffect, useRef } from 'react';
import { Play, Cpu, AlertCircle, MessageCircle, Layout } from 'lucide-react';
import AgentNode from './components/AgentNode';
import OrchestratorNode from './components/OrchestratorNode';
import ConnectionCanvas from './components/ConnectionCanvas';
import AgentOutput from './components/AgentOutput';
import ReportViewer from './components/ReportViewer';
import DialoguePanel from './components/DialoguePanel';

/**
 * AI Startup Studio - Pixel Edition with Dialogue Visualization
 *
 * NEW FEATURES:
 * - Real-time dialogue panel showing orchestrator-agent conversations
 * - Critique/revision rounds visualized with round numbers
 * - Approval (✓) and rejection (✗) indicators
 * - Toggle between visual graph and dialogue view
 * - Physical interaction: active agent orbits to orchestrator and bumps with spark bursts
 */

const AGENT_KEYS = [
  'ideation',
  'market_research',
  'validation',
  'refinement',
  'business_model',
  'report_writer'
];

const AGENT_POSITIONS = {
  ideation: { angle: -90 },
  market_research: { angle: -30 },
  validation: { angle: 30 },
  refinement: { angle: 90 },
  business_model: { angle: 150 },
  report_writer: { angle: 210 }
};

const REST_RADIUS = 280;
const ENGAGED_RADIUS = 150;

// Backend API base URL.
// Configurable via the VITE_API_BASE_URL environment variable (see frontend/.env.example).
// Falls back to localhost:8000 for local development.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function App() {
  const [userInput, setUserInput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [agents, setAgents] = useState({});
  const [agentStatuses, setAgentStatuses] = useState({});
  const [agentOutputs, setAgentOutputs] = useState({});
  const [activeAgent, setActiveAgent] = useState(null);
  const [orchestratorMessage, setOrchestratorMessage] = useState('Idle');
  const [orchestratorActive, setOrchestratorActive] = useState(false);
  const [orchestratorReviewing, setOrchestratorReviewing] = useState(false);
  const [error, setError] = useState(null);
  const [finalReport, setFinalReport] = useState(null);
  const [dataPackets, setDataPackets] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [reportPath, setReportPath] = useState(null);
  const [reportUrl, setReportUrl] = useState(null);
  const [dialogueMessages, setDialogueMessages] = useState([]);
  const [revisionCounts, setRevisionCounts] = useState({});
  const [bumpEvents, setBumpEvents] = useState([]);
  const [orchestratorBumpKey, setOrchestratorBumpKey] = useState(0);

  // Fetch agent metadata
  useEffect(() => {
    fetch(`${API_BASE_URL}/agents`)
      .then(res => res.json())
      .then(data => {
        setAgents(data);
        const initialStatuses = {};
        AGENT_KEYS.forEach(key => {
          initialStatuses[key] = 'pending';
        });
        setAgentStatuses(initialStatuses);
      })
      .catch(err => {
        console.error('Failed to fetch agents:', err);
        setError('Cannot connect to backend. Make sure Python server is running on port 8000.');
      });
  }, []);

  /**
   * Trigger data packet animation between orchestrator and agent
   */
  const animateDataFlow = (fromOrchestrator, agentKey) => {
    const id = Date.now() + Math.random();
    setDataPackets(prev => [...prev, {
      id,
      agentKey,
      direction: fromOrchestrator ? 'out' : 'in'
    }]);

    setTimeout(() => {
      setDataPackets(prev => prev.filter(p => p.id !== id));
    }, 1500);
  };

  /**
   * Trigger a bump/collision animation between orchestrator and agent
   */
  const triggerBump = (agentKey, direction) => {
    if (!agentKey || !AGENT_POSITIONS[agentKey]) return;
    const id = Date.now() + Math.random();
    const angle = AGENT_POSITIONS[agentKey].angle;
    setBumpEvents(prev => [...prev, { id, agentKey, angle, direction }]);
    setOrchestratorBumpKey(k => k + 1);
    setTimeout(() => {
      setBumpEvents(prev => prev.filter(b => b.id !== id));
    }, 700);
  };

  /**
   * Start orchestration with Server-Sent Events
   */
  const startOrchestration = async () => {
    if (!userInput.trim()) {
      setError('Please enter a problem or industry');
      return;
    }

    // Reset state
    setIsRunning(true);
    setError(null);
    setFinalReport(null);
    setReportPath(null);
    setReportUrl(null);
    setAgentOutputs({});
    setDialogueMessages([]);
    setRevisionCounts({});
    const resetStatuses = {};
    AGENT_KEYS.forEach(key => {
      resetStatuses[key] = 'pending';
    });
    setAgentStatuses(resetStatuses);
    setOrchestratorActive(true);
    setOrchestratorMessage('Initiating workflow...');

    try {
      const response = await fetch(`${API_BASE_URL}/orchestrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem: userInput })
      });

      if (!response.ok) {
        throw new Error('Failed to start orchestration');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              handleSSEEvent(data);
            } catch (e) {
              console.error('Failed to parse SSE:', e);
            }
          }
        }
      }
    } catch (err) {
      setError(err.message);
      setOrchestratorActive(false);
    } finally {
      setIsRunning(false);
    }
  };

  /**
   * Handle Server-Sent Events from backend
   */
  const handleSSEEvent = (event) => {
    switch (event.type) {
      case 'start':
        setOrchestratorMessage('Workflow initiated');
        break;

      case 'agent_start':
        setActiveAgent(event.agent);
        setAgentStatuses(prev => ({ ...prev, [event.agent]: 'running' }));
        break;

      case 'agent_thinking':
        setOrchestratorMessage(event.message);
        animateDataFlow(true, event.agent);
        triggerBump(event.agent, 'out');
        break;

      case 'dialogue': {
        // Add to dialogue panel
        setDialogueMessages(prev => [...prev, event]);

        // Update orchestrator message based on speaker
        const targetKey = event.speaker === 'orchestrator' ? event.to : event.speaker;
        if (event.speaker === 'orchestrator') {
          setOrchestratorMessage(`Speaking to ${event.to}...`);
          animateDataFlow(true, event.to);
          triggerBump(event.to, 'out');
        } else {
          setOrchestratorMessage(`${event.speaker} responding...`);
          animateDataFlow(false, event.speaker);
          triggerBump(event.speaker, 'in');
        }

        // Track revisions
        if (event.round > 0) {
          setRevisionCounts(prev => ({
            ...prev,
            [targetKey]: Math.max(prev[targetKey] || 0, event.round)
          }));
        }
        break;
      }

      case 'orchestrator_reviewing':
        setOrchestratorReviewing(true);
        setOrchestratorMessage(`Reviewing ${event.agent}'s work...`);
        triggerBump(event.agent, 'in');
        setTimeout(() => setOrchestratorReviewing(false), 1500);
        break;

      case 'agent_complete':
        setAgentStatuses(prev => ({ ...prev, [event.agent]: 'complete' }));
        setAgentOutputs(prev => ({ ...prev, [event.agent]: event.output }));
        setActiveAgent(null);
        break;

      case 'orchestrator_decision':
        setOrchestratorMessage(event.message);
        break;

      case 'saving_report':
        setOrchestratorMessage(event.message);
        break;

      case 'complete':
        setOrchestratorMessage('Workflow complete!');
        setOrchestratorActive(false);
        if (event.final_state?.report) {
          setFinalReport(event.final_state.report);
        }
        if (event.save_result) {
          setReportPath(event.save_result.filepath);
          setReportUrl(event.save_result.url);
        }
        break;

      case 'error':
        setError(event.message);
        setOrchestratorActive(false);
        break;

      default:
        break;
    }
  };

  const getAgentPosition = (angle, radius = REST_RADIUS) => {
    const radians = (angle * Math.PI) / 180;
    return {
      x: Math.cos(radians) * radius,
      y: Math.sin(radians) * radius
    };
  };

  // Where the active agent currently sits — orchestrator leans this way
  const orchestratorTilt = (() => {
    if (!activeAgent || !AGENT_POSITIONS[activeAgent]) return { x: 0, y: 0 };
    const angle = AGENT_POSITIONS[activeAgent].angle;
    const rad = (angle * Math.PI) / 180;
    return { x: Math.cos(rad) * 14, y: Math.sin(rad) * 14 };
  })();

  const completedCount = Object.values(agentStatuses).filter(s => s === 'complete').length;
  const progress = (completedCount / AGENT_KEYS.length) * 100;

  return (
    <div className="min-h-screen p-6 grid-bg relative">
      {/* Header */}
      <div className="text-center mb-8 relative z-10">
        <h1 className="font-pixel text-2xl md:text-4xl text-white mb-2 tracking-wider">
          AI STARTUP STUDIO
        </h1>
        <p className="font-retro text-xl text-indigo-300">
          ⚡ Demanding Orchestrator with Live Dialogue ⚡
        </p>
      </div>

      {/* Input Section */}
      <div className="max-w-3xl mx-auto mb-8 bg-slate-900/80 backdrop-blur-sm border-2 border-indigo-500/50 rounded-lg p-6 shadow-2xl">
        <label className="block font-pixel text-xs text-indigo-300 mb-3">
          ▶ ENTER PROBLEM/INDUSTRY:
        </label>
        <textarea
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          placeholder="e.g., Sustainable agriculture in East Africa..."
          className="w-full bg-slate-950 border-2 border-indigo-500/30 rounded text-white font-retro text-lg p-3 focus:border-indigo-400 focus:outline-none resize-none"
          rows="2"
          disabled={isRunning}
        />
        <button
          onClick={startOrchestration}
          disabled={isRunning || !userInput.trim()}
          className="mt-4 w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-pixel text-xs py-4 px-6 rounded border-2 border-indigo-400 transition-all flex items-center justify-center gap-3 shadow-lg hover:shadow-indigo-500/50"
        >
          {isRunning ? (
            <>
              <Cpu className="w-5 h-5 animate-spin" />
              ORCHESTRATING...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              START ORCHESTRATION
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="max-w-3xl mx-auto mb-8 bg-red-900/30 border-2 border-red-500 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-pixel text-xs text-red-300 mb-1">ERROR DETECTED</h3>
            <p className="font-retro text-lg text-red-200">{error}</p>
          </div>
        </div>
      )}

      {/* Main Content - Two Column Layout */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-5 gap-6 mb-8">
        {/* Left: Visual Dashboard (3 cols) */}
        <div
          className="lg:col-span-3 relative bg-slate-950/50 backdrop-blur-sm border-2 border-indigo-500/30 rounded-lg p-8 overflow-hidden"
          style={{ minHeight: '700px' }}
        >
          <div className="flex items-center gap-2 mb-4 absolute top-3 left-3 z-30">
            <Layout className="w-4 h-4 text-indigo-300" />
            <h3 className="font-pixel text-[10px] text-indigo-300">
              ORCHESTRATION GRAPH
            </h3>
          </div>

          <ConnectionCanvas
            agents={agents}
            agentStatuses={agentStatuses}
            activeAgent={activeAgent}
            dataPackets={dataPackets}
            getAgentPosition={getAgentPosition}
            engagedRadius={ENGAGED_RADIUS}
            restRadius={REST_RADIUS}
          />

          {/* Spark bursts at impact points */}
          {bumpEvents.map(b => {
            const halfRadius = ENGAGED_RADIUS * 0.55;
            const halfCoords = getAgentPosition(b.angle, halfRadius);
            return (
              <div
                key={b.id}
                className="absolute top-1/2 left-1/2 z-40 pointer-events-none"
                style={{
                  transform: `translate(calc(-50% + ${halfCoords.x}px), calc(-50% + ${halfCoords.y}px))`
                }}
              >
                <SparkBurst />
              </div>
            );
          })}

          {/* Center: Orchestrator */}
          <div
            className="absolute top-1/2 left-1/2 z-20"
            style={{
              transform: `translate(calc(-50% + ${orchestratorTilt.x}px), calc(-50% + ${orchestratorTilt.y}px))`,
              transition: 'transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)'
            }}
          >
            <OrchestratorNode
              isActive={orchestratorActive}
              isReviewing={orchestratorReviewing}
              message={orchestratorMessage}
              progress={progress}
              bumpKey={orchestratorBumpKey}
            />
          </div>

          {/* Surrounding: Agents */}
          {AGENT_KEYS.map((key) => {
            const position = AGENT_POSITIONS[key];
            const isEngaged = activeAgent === key;
            const radius = isEngaged ? ENGAGED_RADIUS : REST_RADIUS;
            const coords = getAgentPosition(position.angle, radius);
            const agent = agents[key];
            if (!agent) return null;

            const bumpForThis = bumpEvents.find(b => b.agentKey === key);

            return (
              <div
                key={key}
                className="absolute top-1/2 left-1/2 z-10"
                style={{
                  transform: `translate(calc(-50% + ${coords.x}px), calc(-50% + ${coords.y}px))`,
                  transition: 'transform 0.7s cubic-bezier(0.34, 1.56, 0.64, 1)'
                }}
              >
                <AgentNode
                  agentKey={key}
                  agent={agent}
                  status={agentStatuses[key] || 'pending'}
                  isActive={activeAgent === key}
                  hasOutput={!!agentOutputs[key]}
                  onClick={() => setSelectedAgent(selectedAgent === key ? null : key)}
                  isSelected={selectedAgent === key}
                  revisionCount={revisionCounts[key] || 0}
                  isEngaged={isEngaged}
                  bumpKey={bumpForThis?.id || 0}
                  bumpAngle={position.angle}
                />
              </div>
            );
          })}
        </div>

        {/* Right: Dialogue Panel (2 cols) */}
        <div className="lg:col-span-2">
          <DialoguePanel
            messages={dialogueMessages}
            agents={agents}
          />
        </div>
      </div>

      {/* Selected Agent Output Display */}
      {selectedAgent && agentOutputs[selectedAgent] && (
        <AgentOutput
          agentKey={selectedAgent}
          agent={agents[selectedAgent]}
          output={agentOutputs[selectedAgent]}
          onClose={() => setSelectedAgent(null)}
        />
      )}

      {/* Final Report */}
      {finalReport && (
        <ReportViewer
          report={finalReport}
          reportPath={reportPath}
          reportUrl={reportUrl}
        />
      )}

      {/* Footer */}
      <div className="text-center mt-12 font-retro text-indigo-400/60">
        <p>Built with Python + FastAPI + React • Powered by Llama 3.3 70B (Hugging Face)</p>
      </div>
    </div>
  );
}

/**
 * Spark burst rendered at the impact point between an agent and the orchestrator.
 */
function SparkBurst() {
  return (
    <div className="spark-burst">
      {Array.from({ length: 10 }).map((_, i) => (
        <span
          key={i}
          className="spark"
          style={{ '--spark-angle': `${i * 36}deg`, '--spark-delay': `${(i % 3) * 30}ms` }}
        />
      ))}
      <span className="spark-flash" />
    </div>
  );
}
