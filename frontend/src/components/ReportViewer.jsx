import React from 'react';
import { FileText, Download, ExternalLink } from 'lucide-react';

/**
 * ReportViewer - Display the final report
 * Now supports Google Docs URL via MCP integration
 */
export default function ReportViewer({ report, reportPath, reportUrl }) {
  const downloadReport = () => {
    const blob = new Blob([report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `startup_report_${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-4xl mx-auto bg-slate-900/90 border-2 border-green-500 rounded-lg p-6 mb-8 shadow-2xl shadow-green-500/20">
      <div className="flex items-center justify-between mb-4 pb-4 border-b border-green-500/30">
        <div className="flex items-center gap-3">
          <FileText className="w-8 h-8 text-green-400" />
          <h2 className="font-pixel text-sm text-green-300">
            FINAL REPORT GENERATED
          </h2>
        </div>
        <div className="flex gap-2">
          {reportUrl && (
            <a
              href={reportUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-blue-600 hover:bg-blue-500 text-white font-pixel text-xs py-2 px-4 rounded border-2 border-blue-400 flex items-center gap-2 transition-all"
            >
              <ExternalLink className="w-4 h-4" />
              GOOGLE DOCS
            </a>
          )}
          <button
            onClick={downloadReport}
            className="bg-green-600 hover:bg-green-500 text-white font-pixel text-xs py-2 px-4 rounded border-2 border-green-400 flex items-center gap-2 transition-all hover:shadow-lg hover:shadow-green-500/50"
          >
            <Download className="w-4 h-4" />
            DOWNLOAD .MD
          </button>
        </div>
      </div>
      
      {reportUrl && (
        <div className="mb-4 p-3 bg-blue-900/20 rounded border border-blue-500/30">
          <p className="font-retro text-base text-blue-300">
            ☁️ Saved to Google Docs: 
            <a href={reportUrl} target="_blank" rel="noopener noreferrer" 
               className="ml-2 text-yellow-300 hover:text-yellow-200 underline">
              View Document →
            </a>
          </p>
        </div>
      )}
      
      {reportPath && !reportUrl && (
        <div className="mb-4 p-3 bg-slate-950 rounded border border-green-500/30">
          <p className="font-retro text-base text-green-300">
            💾 Saved locally: <span className="text-yellow-300">{reportPath}</span>
          </p>
        </div>
      )}
      
      <div className="bg-slate-950 rounded-lg p-6 border border-green-500/30 max-h-[500px] overflow-y-auto">
        <pre className="whitespace-pre-wrap font-retro text-base text-slate-200 leading-relaxed">
          {report}
        </pre>
      </div>
    </div>
  );
}
