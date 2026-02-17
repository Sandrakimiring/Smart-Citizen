"use client";

import { useEffect, useState, useRef } from "react";
import { Scale, Globe, Send, Sparkles, BookOpen, Shield, Gavel, AlertCircle, Menu, X } from "lucide-react";

export default function ChatPage() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Welcome to SmartCitizen AI. I'm here to help you understand Kenyan laws, bills, and your constitutional rights in simple terms. What would you like to know?",
    },
  ]);

  const [input, setInput] = useState("");
  const [language, setLanguage] = useState("English");
  const [isTyping, setIsTyping] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Uncomment this in your Next.js app to redirect users who haven't accepted the disclaimer
  // useEffect(() => {
  //   const hasAccepted = localStorage.getItem("civicDisclaimer");
  //   if (!hasAccepted) {
  //     router.push("/");
  //   }
  // }, [router]);

  const quickTopics = [
    { 
      icon: BookOpen, 
      label: "Constitution", 
      color: "text-blue-600",
      query: "Tell me about the Kenyan Constitution"
    },
    { 
      icon: Shield, 
      label: "Human Rights", 
      color: "text-green-600",
      query: "What are my human rights in Kenya?"
    },
    { 
      icon: Gavel, 
      label: "Finance Bill", 
      color: "text-purple-600",
      query: "Explain the Finance Bill to me"
    },
    { 
      icon: AlertCircle, 
      label: "Police Powers", 
      color: "text-orange-600",
      query: "What are the limits of police powers in Kenya?"
    },
  ];

  const sampleQuestions = [
    "What are my basic constitutional rights?",
    "Explain the Finance Bill in simple terms",
    "What can I do if arrested?",
    "How does freedom of speech work in Kenya?",
  ];

  const handleTopicClick = (query) => {
    setInput(query);
    setSidebarOpen(false); // Close sidebar on mobile after selection
  };

  const getLanguageCode = (lang: string) => {
    switch (lang) {
      case "English":
        return "en";
      case "Swahili":
        return "sw";
      case "Sheng":
        // Sheng doesn't have a standard ISO code; fall back to auto-detect
        return "en";
      default:
        return "en";
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    setIsTyping(true);

    try {
      const response = await fetch("https://smart-citizen-api.onrender.com/api/ask", {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: userMessage,
          language: getLanguageCode(language),
          auto_detect_language: true,
        }),
      });

      if (!response.ok) {
        // Log full error for debugging
        let errorBody: unknown = null;
        try {
          errorBody = await response.json();
        } catch {
          // ignore JSON parse error
        }
        console.error("Error calling /api/ask", {
          status: response.status,
          statusText: response.statusText,
          body: errorBody,
        });

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              "Sorry, I'm having trouble reaching the legal assistant right now. Please try again in a few moments.",
          },
        ]);
        return;
      }

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            data?.answer ||
            "I couldn't find a clear answer from the legal assistant. Please try rephrasing your question.",
        },
      ]);
    } catch (error) {
      // Log real error for debugging
      console.error("Network or unexpected error calling /api/ask", error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, something went wrong while processing your request. Please check your connection and try again.",
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleQuickQuestion = (question) => {
    setInput(question);
    setSidebarOpen(false); // Close sidebar on mobile after selection
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Toggle sidebar"
            >
              <Menu className="h-5 w-5 text-gray-600" />
            </button>
            
            <a href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
              <div className="bg-blue-600 p-2 rounded-lg">
                <Scale className="h-5 w-5 text-white" />
              </div>
              <span className="font-bold text-lg text-gray-900">SmartCitizen AI</span>
            </a>
          </div>

          <div className="flex items-center gap-2 bg-gray-50 px-3 py-2 rounded-lg border border-gray-200">
            <Globe className="h-4 w-4 text-gray-600" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="bg-transparent border-none text-sm font-medium text-gray-700 focus:outline-none cursor-pointer"
            >
              <option>English</option>
              <option>Swahili</option>
              <option>Sheng</option>
            </select>
          </div>
        </div>
      </header>

      <main className="flex flex-1 overflow-hidden relative">
        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <aside
          className={`
            fixed lg:static inset-y-0 left-0 z-40
            w-72 bg-white border-r border-gray-200 p-6 overflow-y-auto
            transform transition-transform duration-300 ease-in-out
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          `}
        >
          <div className="flex justify-between items-center mb-6 lg:hidden">
            <h2 className="font-bold text-gray-900">Menu</h2>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="h-5 w-5 text-gray-600" />
            </button>
          </div>

          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-blue-600" />
                Quick Topics
              </h3>
              <ul className="space-y-2">
                {quickTopics.map((topic, i) => (
                  <li key={i}>
                    <button 
                      onClick={() => handleTopicClick(topic.query)}
                      className="w-full text-left px-3 py-2 rounded-lg hover:bg-blue-50 transition-colors flex items-center gap-2 text-sm group"
                    >
                      <topic.icon className={`h-4 w-4 ${topic.color}`} />
                      <span className="text-gray-700 group-hover:text-blue-600 font-medium">
                        {topic.label}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            <div className="pt-6 border-t border-gray-200">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">
                Sample Questions
              </h3>
              <div className="space-y-2">
                {sampleQuestions.map((question, i) => (
                  <button
                    key={i}
                    onClick={() => handleQuickQuestion(question)}
                    className="w-full text-left px-3 py-2 text-xs text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  >
                    "{question}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        </aside>

        {/* Chat Area */}
        <section className="flex flex-col flex-1 bg-white w-full">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-2xl px-5 py-4 rounded-2xl text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white shadow-md"
                      : "bg-gray-100 text-gray-800 border border-gray-200"
                  }`}
                >
                  {msg.role === "assistant" && (
                    <div className="flex items-center gap-2 mb-2 text-blue-600">
                      <Scale className="h-4 w-4" />
                      <span className="font-semibold text-xs">SmartCitizen AI</span>
                    </div>
                  )}
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-100 border border-gray-200 px-5 py-4 rounded-2xl">
                  <div className="flex items-center gap-2 mb-2 text-blue-600">
                    <Scale className="h-4 w-4" />
                    <span className="font-semibold text-xs">SmartCitizen AI</span>
                  </div>
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 bg-white p-4 sm:p-6">
            <div className="max-w-4xl mx-auto space-y-3">
              <div className="flex gap-3">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about laws, bills, or your constitutional rights..."
                  className="flex-1 border-2 border-gray-300 rounded-xl px-4 py-3 text-sm text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                />
                <button
                  onClick={sendMessage}
                  disabled={!input.trim()}
                  className="bg-blue-600 text-white px-5 py-3 rounded-xl hover:bg-blue-700 transition-colors shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
                >
                  <Send className="h-4 w-4" />
                  <span className="hidden sm:inline">Send</span>
                </button>
              </div>
              
              <p className="text-xs text-gray-500 flex items-start gap-2">
                <AlertCircle className="h-3 w-3 mt-0.5 flex-shrink-0" />
                <span>
                  Information provided is simplified for civic education. For binding legal interpretation, 
                  consult official sources or a qualified legal professional.
                </span>
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}