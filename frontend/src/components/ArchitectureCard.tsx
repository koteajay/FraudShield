import React from 'react';
import { Layers, Database, Code2 } from 'lucide-react';

export const ArchitectureCard: React.FC = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Layers className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-white">Backend Layer</h3>
        </div>
        <p className="text-xs text-slate-400 mb-3">
          FastAPI microservice with CORS middleware, lifespan events, and Pydantic configuration.
        </p>
        <div className="space-y-1 text-xs font-mono text-slate-300">
          <div className="bg-slate-950/50 px-2.5 py-1.5 rounded border border-slate-800/80">
            GET /health → &#123;"status": "ok"&#125;
          </div>
          <div className="bg-slate-950/50 px-2.5 py-1.5 rounded border border-slate-800/80">
            GET /api → Service info
          </div>
        </div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Database className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-white">Data Foundation</h3>
        </div>
        <p className="text-xs text-slate-400 mb-3">
          SQLAlchemy 2.0 with SQLite database engine and session dependency generator.
        </p>
        <div className="space-y-1 text-xs font-mono text-slate-300">
          <div className="bg-slate-950/50 px-2.5 py-1.5 rounded border border-slate-800/80">
            Engine: sqlite:///./fraudshield.db
          </div>
          <div className="bg-slate-950/50 px-2.5 py-1.5 rounded border border-slate-800/80">
            Models: Reserved for Phase 1+
          </div>
        </div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Code2 className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-white">Client Interface</h3>
        </div>
        <p className="text-xs text-slate-400 mb-3">
          React 19 + Vite + TypeScript application configured with environment variables.
        </p>
        <div className="space-y-1 text-xs font-mono text-slate-300">
          <div className="bg-slate-950/50 px-2.5 py-1.5 rounded border border-slate-800/80">
            Base URL: VITE_API_BASE_URL
          </div>
          <div className="bg-slate-950/50 px-2.5 py-1.5 rounded border border-slate-800/80">
            Hot Module Reloading (Vite)
          </div>
        </div>
      </div>
    </div>
  );
};
