import apiClient from "@/lib/axios";

export const getDashboardStats = async () => {
  const { data } = await apiClient.get("/dashboard/stats");
  return data;
};

export const getRecentPatients = async () => {
  const { data } = await apiClient.get("/patients?limit=5");
  return data;
};

export const getTodayAppointments = async () => {
  const { data } = await apiClient.get("/appointments/today");
  return data;
};

export const getAIAlerts = async () => {
  const { data } = await apiClient.get("/dashboard/ai-alerts");
  return data;
};