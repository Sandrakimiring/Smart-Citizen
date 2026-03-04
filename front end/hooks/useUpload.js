import { useState } from "react";


export function useUpload() {
const [uploading, setUploading] = useState(false);


const uploadFile = async (file) => {
setUploading(true);
const formData = new FormData();
formData.append("file", file);


await fetch("http://localhost:8000/upload", {
method: "POST",
body: formData,
});
setUploading(false);
};


return { uploadFile, uploading };
}