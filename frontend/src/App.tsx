import React, { useState } from 'react';
import { Shield, Lock, Activity, Database } from 'lucide-react';

export default function App() {
  const [valuation] = useState<number>(142850420.50);
  const [cryptographicHash] = useState<string>("f49a8bc2e1...");

  return (
    <div className="min-h-screen bg-[#0A0B0E] text-[#E2E8F0] font-sans antialiased p-8 selection:bg-[#D4AF37] selection:text-black">
      <header className="flex justify-between items-center border-b border-[#1E222B] pb-6 mb-10">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#1E222B] to-[#12141A] border border-[#D4AF37]/30 flex items-center justify-center shadow-lg">
            <span className="font-serif text-[#D4AF37] font-bold text-lg">8</span>
          </div>
          <div>
            <h1 className="text-xl font-medium tracking-wide text-white">8above.pro</h1>
            <p className="text-xs text-[#8A95A5] uppercase tracking-widest font-mono">Sovereign Institutional Ledger</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-[#12141A] border border-[#1E222B] px-3 py-1.5 rounded-full">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-xs font-mono text-[#8A95A5]">SSOT SYNCED</span>
          </div>
          <div className="bg-[#12141A] border border-[#D4AF37]/20 px-3 py-1.5 rounded-md text-xs font-mono text-[#D4AF37]">
            TENANT: ISOLATED_ROOT
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto space-y-8">
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-b from-[#161922] to-[#0F1117] border border-[#D4AF37]/40 p-8 shadow-2xl">
          <div className="absolute top-0 right-0 p-6 opacity-10">
            <Shield className="w-32 h-32 text-[#D4AF37]" />
          </div>

          <div className="relative z-10">
            <div className="flex items-center space-x-2 text-[#D4AF37] mb-2">
              <Lock className="w-4 h-4" />
              <span className="text-xs font-mono uppercase tracking-wider">Consolidated Net Asset Valuation</span>
            </div>

            <div className="text-5xl lg:text-6xl font-serif tracking-tight text-white mb-4">
              ${valuation.toLocaleString('en-US', { minimumFractionDigits: 2 })} <span className="text-2xl text-[#8A95A5] font-sans">USD</span>
            </div>

            <div className="flex flex-wrap items-center justify-between pt-4 border-t border-[#1E222B]/60 text-xs font-mono text-[#8A95A5]">
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-[#D4AF37]" />
                <span>Real-time reconciliation across Global Custodians. Zero variance detected.</span>
              </div>
              <div className="mt-2 sm:mt-0 text-[#D4AF37] bg-[#D4AF37]/10 px-2.5 py-1 rounded border border-[#D4AF37]/20">
                Immutable Ledger Checksum: #{cryptographicHash}
              </div>
            </div>
          </div>
        </div>

        <section>
          <h2 className="text-sm font-mono uppercase tracking-wider text-[#8A95A5] mb-4">Verified Custodian Nodes</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-[#12141A] border border-[#1E222B] rounded-xl p-6 hover:border-[#D4AF37]/30 transition-all">
              <div className="flex justify-between items-start mb-4">
                <span className="text-sm font-medium text-white">Swiss Custody A</span>
                <Database className="w-4 h-4 text-[#D4AF37]" />
              </div>
              <div className="text-2xl font-serif text-white mb-2">$64,120,000</div>
              <div className="text-xs font-mono text-[#8A95A5]">Verified Hash: #f49a...</div>
            </div>

            <div className="bg-[#12141A] border border-[#1E222B] rounded-xl p-6 hover:border-[#D4AF37]/30 transition-all">
              <div className="flex justify-between items-start mb-4">
                <span className="text-sm font-medium text-white">DIFC Regional Hub</span>
                <Database className="w-4 h-4 text-[#D4AF37]" />
              </div>
              <div className="text-2xl font-serif text-white mb-2">$51,430,420</div>
              <div className="text-xs font-mono text-[#8A95A5]">Verified Hash: #56a1...</div>
            </div>

            <div className="bg-[#12141A] border border-[#1E222B] rounded-xl p-6 hover:border-[#D4AF37]/30 transition-all">
              <div className="flex justify-between items-start mb-4">
                <span className="text-sm font-medium text-white">Liquid Yield / Reserves</span>
                <Database className="w-4 h-4 text-[#D4AF37]" />
              </div>
              <div className="text-2xl font-serif text-white mb-2">$27,300,000</div>
              <div className="text-xs font-mono text-[#8A95A5]">Verified Hash: #3c9e...</div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
