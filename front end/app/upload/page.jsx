"use client";

import { useState } from "react";
import { Scale, FileText, Upload, CheckCircle, AlertCircle, FileCheck } from "lucide-react";

export default function Page() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadComplete, setUploadComplete] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setUploadComplete(false);
    }
  };

  const handleUpload = () => {
    if (!file) return;
    
    setUploading(true);
    
    // Simulate upload process
    setTimeout(() => {
      setUploading(false);
      setUploadComplete(true);
    }, 2000);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && droppedFile.type === "application/pdf") {
      setFile(droppedFile);
      setUploadComplete(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <a href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity w-fit">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Scale className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold text-lg text-gray-900">SmartCitizen AI</span>
          </a>
        </div>
      </header>

      {/* Main Upload Area */}
      <main className="flex-1 flex items-center justify-center px-4 sm:px-6 py-12">
        <div className="w-full max-w-2xl space-y-8">
          {/* Title Section */}
          <div className="text-center space-y-3">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-2">
              <FileText className="h-8 w-8 text-blue-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900">
              Upload Legal Document
            </h1>
            <p className="text-gray-600 text-lg">
              Upload bills, policies, or gazette notices for AI-powered analysis
            </p>
          </div>

          {/* Upload Card */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
            <div className="p-8 space-y-6">
              {/* Drag & Drop Area */}
              <div
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className={`
                  border-2 border-dashed rounded-xl p-12 text-center transition-all
                  ${file ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'}
                  cursor-pointer
                `}
              >
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={handleFileChange}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer space-y-4 block">
                  {!file ? (
                    <>
                      <div className="flex justify-center">
                        <div className="bg-blue-100 p-4 rounded-full">
                          <Upload className="h-8 w-8 text-blue-600" />
                        </div>
                      </div>
                      <div>
                        <p className="text-lg font-semibold text-gray-700 mb-1">
                          Drop your PDF here or click to browse
                        </p>
                        <p className="text-sm text-gray-500">
                          Maximum file size: 10MB
                        </p>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex justify-center">
                        <div className="bg-green-100 p-4 rounded-full">
                          <FileCheck className="h-8 w-8 text-green-600" />
                        </div>
                      </div>
                      <div>
                        <p className="text-lg font-semibold text-gray-900 mb-1">
                          {file.name}
                        </p>
                        <p className="text-sm text-gray-500">
                          {formatFileSize(file.size)} • Click to change file
                        </p>
                      </div>
                    </>
                  )}
                </label>
              </div>

              {/* Upload Status */}
              {uploadComplete && (
                <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-lg p-4">
                  <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-green-900">Upload Complete!</p>
                    <p className="text-xs text-green-700">Your document is ready for analysis</p>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleUpload}
                  disabled={!file || uploading}
                  className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-blue-600/20"
                >
                  {uploading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="h-5 w-5" />
                      <span>Upload & Analyze</span>
                    </>
                  )}
                </button>
                
                <a
                  href="/chat"
                  className="px-6 py-3 rounded-xl font-semibold border-2 border-gray-300 hover:border-gray-400 hover:bg-gray-50 transition-colors text-center"
                >
                  Ask Questions Instead
                </a>
              </div>

              {/* Info Section */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex gap-3">
                  <AlertCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-blue-900">What you can upload:</p>
                    <ul className="text-xs text-blue-800 space-y-1">
                      <li>• Government bills and proposed legislation</li>
                      <li>• Policy documents and public notices</li>
                      <li>• Kenya Gazette publications</li>
                      <li>• Legal documents in PDF format only</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid sm:grid-cols-3 gap-4">
            <FeatureBox
              icon="🔍"
              title="Deep Analysis"
              description="AI-powered document comprehension"
            />
            <FeatureBox
              icon="📊"
              title="Key Points"
              description="Extract critical information"
            />
            <FeatureBox
              icon="💬"
              title="Ask Questions"
              description="Interactive Q&A about content"
            />
          </div>
        </div>
      </main>
    </div>
  );
}

function FeatureBox({ icon, title, description }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
      <div className="text-2xl mb-2">{icon}</div>
      <h3 className="font-semibold text-sm text-gray-900 mb-1">{title}</h3>
      <p className="text-xs text-gray-600">{description}</p>
    </div>
  );
}