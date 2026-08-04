import api from "@/lib/axios";

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
}

export const login = async (data: LoginData) => {
  const form = new URLSearchParams();

  form.append("username", data.email);
  form.append("password", data.password);

  const response = await api.post(
    "/auth/login",
    form,
    {
      headers: {
        "Content-Type":
          "application/x-www-form-urlencoded",
      },
    }
  );

  return response.data;
};

export const register = async (
  data: RegisterData
) => {
  const response = await api.post(
    "/auth/register",
    data
  );

  return response.data;
};

export const me = async () => {
  const response = await api.get("/auth/me");

  return response.data;
};