import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { useAuth } from "./AuthContext";
import { ApiError } from "../../lib/api-client";

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [targetRole, setTargetRole] = useState("Software Engineer (Backend)");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    try {
      await register({
        email: email.trim().toLowerCase(),
        password,
        full_name: fullName.trim(),
        target_role: targetRole,
        experience_level: "intermediate",
      });
      navigate("/dashboard");
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <Card className="w-full max-w-md" title="Create your CareerPilot Account" subtitle="Prepare for your technical career">
        {errorMessage && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
            {errorMessage}
          </div>
        )}

        <form className="space-y-4 mt-2" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-slate-700">Full Name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Jane Doe"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="candidate@university.edu"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Target Role</label>
            <select
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="Software Engineer (Backend)">Software Engineer (Backend)</option>
              <option value="Software Engineer (Full Stack)">Software Engineer (Full Stack)</option>
              <option value="Frontend Engineer">Frontend Engineer</option>
              <option value="Data Engineer">Data Engineer</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="•••••••• (minimum 8 characters)"
              minLength={8}
              required
            />
          </div>
          <Button type="submit" isLoading={isLoading} className="w-full">
            Register Account
          </Button>
          <p className="text-center text-xs text-slate-500 mt-3">
            Already have an account?{" "}
            <Link to="/login" className="text-blue-600 font-medium hover:underline">
              Sign In
            </Link>
          </p>
        </form>
      </Card>
    </div>
  );
};
