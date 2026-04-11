import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;

export const fetchDocuments = async () => {
  const response = await api.get('/api/documents/');
  return response.data;
};

export const fetchStats = async () => {
  const response = await api.get('/api/stats');
  return response.data;
};

export const uploadDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/api/documents/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const deleteDocument = async (id: string) => {
  await api.delete(`/api/documents/${id}`);
};

export const queryChat = async (message: string, history: any[]) => {
  const response = await api.post('/api/chat', {
    message,
    history,
  });
  return response.data;
};
