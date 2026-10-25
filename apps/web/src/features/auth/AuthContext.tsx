import React, { createContext, useContext, useEffect, useState } from "react";
import { User } from "./types";
import { getCurrentUser } from "./api/get-user";
import { loginWithCredentials, LoginCredentials } from "./api/login";
import { registerCandidate, RegisterPayload } from "./api/register";
import { logoutCandidate } from "./api/logout";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    getCurrentUser()
      .then((data) => setUser(data))
      .finally(() => setIsLoading(false));
  }, []);

  const login = async (credentials: LoginCredentials) => {
    const res = await loginWithCredentials(credentials);
    setUser(res.user);
  };

  const register = async (payload: RegisterPayload) => {
    const res = await registerCandidate(payload);
    setUser(res.user);
  };

  const logout = async () => {
    await logoutCandidate();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
