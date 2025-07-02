// ConroeISD_AI_Chatbot.jsx
// React chatbot UI with GPT + voice + user-defined rule logic + animated avatar

import React, { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const ConroeISDChatbot = () => {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hi! I'm your Conroe ISD Tech Support Assistant. How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const utteranceRef = useRef(null);

  // 📚 Define rule-based responses
  const rules = [
    { keyword: "password", response: "It sounds like you need help resetting your password. Let me guide you through that." },
    { keyword: "wifi", response: "Let’s troubleshoot your Wi-Fi connection. Is your device connected to the correct network?" },
    { keyword: "chromebook", response: "If your Chromebook won't turn on, try holding the power button for 10 seconds." },
  ];

  const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = window.speechSynthesis.getVoices().find(v => v.name.includes("Female") || v.name.includes("Google")) || null;
    utterance.rate = 1;
    window.speechSynthesis.speak(utterance);
    utteranceRef.current = utterance;
  };

  const findRuleResponse = (text) => {
    for (let rule of rules) {
      if (text.toLowerCase().includes(rule.keyword)) {
        return rule.response;
      }
    }
    return null;
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    const newMessage = { sender: "user", text: input };
    setMessages(prev => [...prev, newMessage]);
    setInput("");
    setIsLoading(true);

    // Check rule-based response first
    const ruleResponse = findRuleResponse(input);
    if (ruleResponse) {
      const botMessage = { sender: "bot", text: ruleResponse };
      setMessages(prev => [...prev, botMessage]);
      speak(ruleResponse);
      setIsLoading(false);
      return;
    }

    // Else fallback to GPT-4
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer YOUR_OPENAI_API_KEY`,
      },
      body: JSON.stringify({
        model: "gpt-4",
        messages: [
          { role: "system", content: "You are a helpful, friendly Tier 1 tech support agent for Conroe ISD." },
          ...messages.map((msg) => ({ role: msg.sender === "bot" ? "assistant" : "user", content: msg.text })),
          { role: "user", content: input },
        ],
      }),
    });

    const data = await response.json();
    const botText = data.choices[0].message.content;
    const botMessage = { sender: "bot", text: botText };
    setMessages((prev) => [...prev, botMessage]);
    speak(botText);
    setIsLoading(false);
  };

  return (
    <div className="w-full max-w-3xl mx-auto p-4">
      <div className="flex items-center space-x-4 mb-4">
        <img
          src="/avatar-conroeisd.png" // your avatar image goes here
          alt="AI Assistant"
          className="w-24 h-24 rounded-full border object-cover"
        />
        <h2 className="text-xl font-semibold">Conroe ISD Tech Assistant</h2>
      </div>

      <div className="bg-white rounded-lg p-4 shadow h-96 overflow-y-scroll">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`my-2 ${msg.sender === "bot" ? "text-left text-blue-900" : "text-right text-gray-700"}`}
          >
            <span className="block bg-gray-100 inline-block px-3 py-2 rounded">
              {msg.text}
            </span>
          </div>
        ))}
        {isLoading && <p className="text-gray-400">Typing...</p>}
      </div>

      <div className="flex items-center mt-4 gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a tech support question..."
          className="flex-1"
        />
        <Button onClick={handleSend}>Send</Button>
      </div>

      <div className="mt-6 p-4 bg-blue-50 rounded">
        <h3 className="font-bold mb-2">🛠️ Rule-Based Responses</h3>
        <ul className="list-disc pl-5 text-sm text-gray-700">
          {rules.map((rule, i) => (
            <li key={i}><strong>If user says</strong> "{rule.keyword}" → <strong>Respond:</strong> {rule.response}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default ConroeISDChatbot;
