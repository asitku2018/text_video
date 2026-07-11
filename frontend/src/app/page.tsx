"use client";

import { useState, useRef } from "react";

export default function Home() {
  const [image, setImage] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleGenerate = async () => {
    if (!image || !text) return alert("Please provide an image and text.");
    
    setLoading(true);
    setStatus("Uploading...");
    setVideoUrl(null);

    const formData = new FormData();
    formData.append("image", image);
    formData.append("text", text);
    formData.append("language", language);

    try {
      const res = await fetch("http://localhost:8000/api/v1/videos/generate", {
        method: "POST",
        body: formData,
      });
      
      if (!res.ok) throw new Error("Upload failed");
      
      const data = await res.json();
      pollStatus(data.task_id);
    } catch (err) {
      setStatus("Error occurred.");
      setLoading(false);
    }
  };

  const pollStatus = async (taskId: string) => {
    setStatus("Processing...");
    const interval = setInterval(async () => {
      const res = await fetch(`http://localhost:8000/api/v1/videos/status/${taskId}`);
      const data = await res.json();

      if (data.status === "COMPLETED") {
        clearInterval(interval);
        setVideoUrl(`http://localhost:8000${data.video_url}`);
        setStatus("Ready!");
        setLoading(false);
      } else if (data.status === "FAILED") {
        clearInterval(interval);
        setStatus("Rendering failed.");
        setLoading(false);
      }
    }, 2000);
  };

  return (
    <main className="min-h-screen p-10 bg-gray-50 text-gray-900 flex flex-col items-center">
      <h1 className="text-3xl font-bold mb-8">AI Audio-Visualizer</h1>
      
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Banner Image</label>
          <input 
            type="file" 
            accept="image/jpeg, image/png, image/webp"
            onChange={(e) => setImage(e.target.files?.[0] || null)}
            className="mt-1 block w-full border p-2 rounded"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Speech Text</label>
          <textarea 
            rows={4}
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="mt-1 block w-full border p-2 rounded"
            placeholder="Enter text to convert to speech..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Language</label>
          <select 
            value={language} 
            onChange={(e) => setLanguage(e.target.value)}
            className="mt-1 block w-full border p-2 rounded"
          >
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="hi">Hindi</option>
          </select>
        </div>

        <button 
          onClick={handleGenerate}
          disabled={loading}
          className="w-full bg-blue-600 text-white font-bold py-2 px-4 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? status : "Generate Video"}
        </button>
      </div>

      {videoUrl && (
        <div className="mt-10 w-full max-w-md bg-white rounded-xl shadow-lg p-6 flex flex-col items-center">
          <h2 className="text-xl font-bold mb-4">Your Video</h2>
          <video controls className="w-full rounded mb-4">
            <source src={videoUrl} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
          <a 
            href={videoUrl} 
            download 
            className="bg-green-600 text-white font-bold py-2 px-4 rounded hover:bg-green-700 w-full text-center"
          >
            Download MP4
          </a>
        </div>
      )}
    </main>
  );
}
