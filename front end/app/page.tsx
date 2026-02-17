"use client";

import { useState, useEffect } from "react";
import { Scale, BookOpen, Upload, CheckCircle } from "lucide-react";

export default function Page() {
  const [showDisclaimer, setShowDisclaimer] = useState(false);

  useEffect(() => {
    const accepted = localStorage.getItem("civicDisclaimer");
    if (!accepted) setShowDisclaimer(true);
  }, []);

  const acceptDisclaimer = () => {
    localStorage.setItem("civicDisclaimer", "true");
    setShowDisclaimer(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <Scale className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">SmartCitizen AI</h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="max-w-4xl w-full space-y-12">
          {/* Hero Section */}
          <div className="text-center space-y-6">
            <div className="inline-block">
              <span className="bg-blue-100 text-blue-700 px-4 py-2 rounded-full text-sm font-medium">
                Legal Information Made Simple
              </span>
            </div>
            
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 leading-tight">
              Understand Laws, Bills & Your Rights
            </h2>
            
            <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
              SmartCitizen AI helps Kenyans navigate constitutional rights, government bills, 
              and public policies using clear, accessible language.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row justify-center gap-4 max-w-lg mx-auto">
            <a
              href="/chat"
              className="flex items-center justify-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow-lg shadow-blue-600/20"
            >
              <BookOpen className="h-5 w-5" />
              Ask the Law
            </a>
            <a
              href="/upload"
              className="flex items-center justify-center gap-2 bg-white text-gray-700 px-8 py-4 rounded-xl font-semibold border-2 border-gray-300 hover:border-gray-400 hover:bg-gray-50 transition-colors"
            >
              <Upload className="h-5 w-5" />
              Upload a Bill
            </a>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-6 mt-16">
            <FeatureCard
              icon="📜"
              title="Constitutional Rights"
              description="Learn about your fundamental rights and freedoms under Kenyan law"
            />
            <FeatureCard
              icon="📋"
              title="Bill Analysis"
              description="Get plain-language summaries of proposed legislation and policies"
            />
            <FeatureCard
              icon="💬"
              title="AI-Powered Answers"
              description="Ask questions and receive accurate, easy-to-understand explanations"
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center">
          <p className="text-sm text-gray-500">
            Empowering informed citizenship through accessible legal information
          </p>
        </div>
      </footer>

      {/* Disclaimer Modal */}
      {showDisclaimer && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-6 text-white">
              <div className="flex items-center gap-3">
                <Scale className="h-8 w-8" />
                <h3 className="text-2xl font-bold">Important Notice</h3>
              </div>
            </div>
            
            <div className="p-8 space-y-6">
              <div className="space-y-4 text-gray-700 leading-relaxed">
                <p className="font-medium text-lg text-gray-900">
                  Before you continue:
                </p>
                <p>
                  SmartCitizen AI provides <strong>simplified legal information</strong> for 
                  educational purposes only. This service is designed to help you understand 
                  complex legal topics more easily.
                </p>
                <p>
                  For official legal advice or binding interpretations, please consult:
                </p>
                <ul className="space-y-2 ml-4">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                    <span>Official government sources and publications</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                    <span>A qualified legal professional or lawyer</span>
                  </li>
                </ul>
              </div>
              
              <button
                onClick={acceptDisclaimer}
                className="w-full bg-blue-600 text-white px-6 py-4 rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow-lg"
              >
                I Understand & Continue
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="bg-white p-6 rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-sm leading-relaxed">{description}</p>
    </div>
  );
}