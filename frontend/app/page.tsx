"use client";

import React, { useState, useEffect } from "react";
import {
  Users,
  FileText,
  Search,
  CheckCircle,
  Activity,
  Upload,
  Briefcase,
  Brain,
  Zap,
  Cpu,
  Network,
  Sparkles,
  ArrowRight,
  Play,
  Settings,
  BarChart3
} from "lucide-react";

export default function Dashboard() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentAgent, setCurrentAgent] = useState("Idle");

  const stats = [
    { name: "Active Candidates", value: "0", icon: Users, color: "text-[#8c6763]", bgColor: "bg-[#efe2df]" },
    { name: "AI Matches", value: "0", icon: Brain, color: "text-[#a5642d]", bgColor: "bg-[#f1e3d5]" },
    { name: "Processing Queue", value: "0", icon: Activity, color: "text-[#7f7068]", bgColor: "bg-[#e7e2de]" },
    { name: "Jobs Discovered", value: "0", icon: Briefcase, color: "text-[#5f7a68]", bgColor: "bg-[#e4ece5]" },
  ];

  const agents = [
    { name: "CV Parser", status: "Ready", icon: FileText, color: "text-[#5f7a68]" },
    { name: "Job Searcher", status: "Ready", icon: Search, color: "text-[#7f7068]" },
    { name: "AI Matcher", status: "Ready", icon: Brain, color: "text-[#8c6763]" },
    { name: "Application Generator", status: "Ready", icon: Sparkles, color: "text-[#a5642d]" },
  ];

  const handleStartWorkflow = () => {
    setIsProcessing(true);
    setCurrentAgent("Initializing...");
    // Simulate agent progression
    const agentSequence = ["CV Parser", "Job Searcher", "AI Matcher", "Application Generator"];
    let index = 0;
    const interval = setInterval(() => {
      if (index < agentSequence.length) {
        setCurrentAgent(agentSequence[index]);
        index++;
      } else {
        setIsProcessing(false);
        setCurrentAgent("Complete");
        clearInterval(interval);
      }
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-[#b8b8b6] neural-bg">
      {/* Header */}
      <header className="bg-[#efefed]/90 backdrop-blur-lg border-b border-[#d1cfca]/70 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="ai-glow p-2 bg-[#8c6763] rounded-lg">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-[#8c6763]">
                  INTERLEV AI
                </h1>
                <p className="text-xs text-slate-500">Autonomous Recruitment Platform</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm">
                <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-slate-600">System Online</span>
              </div>
              <button className="p-2 text-slate-400 hover:text-slate-600 transition-colors">
                <Settings className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main Dashboard */}
          <div className="lg:col-span-3 space-y-8">
            {/* Welcome Section */}
            <div className="ai-card rounded-2xl p-8 shadow-xl">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-3xl font-bold text-slate-900 mb-2">
                    Welcome to the Future of Recruitment
                  </h2>
                  <p className="text-slate-600 text-lg">
                    Our AI agents work autonomously to match candidates with perfect opportunities,
                    streamlining the entire recruitment process.
                  </p>
                </div>
                <div className="hidden md:block">
                  <div className="relative">
                    <Network className="h-16 w-16 text-[#8c6763] opacity-20" />
                    <div className="absolute inset-0 animate-pulse">
                      <Sparkles className="h-8 w-8 text-[#a5642d] absolute top-2 right-2" />
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-4">
                <button
                  onClick={handleStartWorkflow}
                  disabled={isProcessing}
                  className="ai-button text-white px-8 py-4 rounded-xl font-semibold flex items-center justify-center space-x-3 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isProcessing ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                      <span>Processing with AI...</span>
                    </>
                  ) : (
                    <>
                      <Play className="h-5 w-5" />
                      <span>Launch AI Recruitment</span>
                    </>
                  )}
                </button>
                <button className="bg-[#f3f3f0] border-2 border-[#d1cfca] text-[#20201e] px-8 py-4 rounded-xl font-semibold hover:border-[#8c6763]/50 transition-colors flex items-center space-x-3">
                  <Upload className="h-5 w-5" />
                  <span>Upload CV</span>
                </button>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {stats.map((stat, index) => (
                <div key={stat.name} className="ai-card rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                  <div className="flex items-center justify-between mb-4">
                    <div className={`p-3 ${stat.bgColor} rounded-lg ${stat.color}`}>
                      <stat.icon size={24} />
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-slate-900">{stat.value}</div>
                      <div className="text-sm text-slate-500">{stat.name}</div>
                    </div>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div className="bg-[#8c6763] h-2 rounded-full" style={{width: '0%'}}></div>
                  </div>
                </div>
              ))}
            </div>

            {/* Agent Status */}
            <div className="ai-card rounded-2xl p-8 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
                  <Cpu className="h-6 w-6 text-[#8c6763]" />
                  <span>AI Agent Status</span>
                </h3>
                <div className="flex items-center space-x-2 text-sm text-slate-500">
                  <Zap className="h-4 w-4" />
                  <span>Real-time Updates</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {agents.map((agent, index) => (
                  <div key={agent.name} className="flex items-center justify-between p-4 bg-slate-50/50 rounded-lg border border-slate-200/50">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 bg-white rounded-lg ${agent.color}`}>
                        <agent.icon size={16} />
                      </div>
                      <div>
                        <div className="font-medium text-slate-900">{agent.name}</div>
                        <div className="text-sm text-slate-500">{agent.status}</div>
                      </div>
                    </div>
                    <div className={`h-3 w-3 rounded-full ${agent.status === 'Ready' ? 'bg-green-500' : 'bg-slate-400'}`}></div>
                  </div>
                ))}
              </div>

              {isProcessing && (
                <div className="mt-6 p-4 bg-[#efe2df] border border-[#d7c4c0] rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-[#8c6763] border-t-transparent"></div>
                    <span className="text-[#8c6763] font-medium">
                      Currently processing with: <span className="font-bold">{currentAgent}</span>
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="ai-card rounded-2xl p-6 shadow-xl">
              <h4 className="font-bold text-slate-900 mb-4 flex items-center space-x-2">
                <BarChart3 className="h-5 w-5 text-[#8c6763]" />
                <span>Quick Actions</span>
              </h4>
              <div className="space-y-3">
                <button className="w-full text-left p-3 rounded-lg hover:bg-slate-50 transition-colors flex items-center space-x-3 text-slate-700">
                  <Users className="h-4 w-4" />
                  <span>View Candidates</span>
                  <ArrowRight className="h-4 w-4 ml-auto" />
                </button>
                <button className="w-full text-left p-3 rounded-lg hover:bg-slate-50 transition-colors flex items-center space-x-3 text-slate-700">
                  <Search className="h-4 w-4" />
                  <span>Job Search</span>
                  <ArrowRight className="h-4 w-4 ml-auto" />
                </button>
                <button className="w-full text-left p-3 rounded-lg hover:bg-slate-50 transition-colors flex items-center space-x-3 text-slate-700">
                  <CheckCircle className="h-4 w-4" />
                  <span>Review Queue</span>
                  <ArrowRight className="h-4 w-4 ml-auto" />
                </button>
                <button className="w-full text-left p-3 rounded-lg hover:bg-slate-50 transition-colors flex items-center space-x-3 text-slate-700">
                  <FileText className="h-4 w-4" />
                  <span>Agent Logs</span>
                  <ArrowRight className="h-4 w-4 ml-auto" />
                </button>
              </div>
            </div>

            {/* System Health */}
            <div className="ai-card rounded-2xl p-6 shadow-xl">
              <h4 className="font-bold text-slate-900 mb-4 flex items-center space-x-2">
                <Activity className="h-5 w-5 text-green-600" />
                <span>System Health</span>
              </h4>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">API Status</span>
                  <div className="flex items-center space-x-2">
                    <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-green-600">Online</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Database</span>
                  <div className="flex items-center space-x-2">
                    <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-green-600">Connected</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">AI Models</span>
                  <div className="flex items-center space-x-2">
                    <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-green-600">Ready</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
