import { useState } from "react";
import { api } from "../lib/api";


export function useChat() {
const [loading, setLoading] = useState(false);


const askQuestion = async (message, language) => {
setLoading(true);
try {
const res = await api.post("/ask", { message, language });
return res.answer;
} finally {
setLoading(false);
}
};


return { askQuestion, loading };
}