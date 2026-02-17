export const api = {
post: async (path, body) => {
const res = await fetch(`http://localhost:8000${path}`, {
method: "POST",
headers: { "Content-Type": "application/json" },
body: JSON.stringify(body),
});
return res.json();
},
};