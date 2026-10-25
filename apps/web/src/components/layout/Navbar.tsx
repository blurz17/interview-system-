import React from "react";
import { Link } from "react-router-dom";
import { Terminal, LogOut, User as UserIcon } from "lucide-react";
import { useAuth } from "../../features/auth/AuthContext";
import { Button } from "../ui/Button";

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-2 font-bold text-xl text-blue-600">
              <Terminal className="h-6 w-6" />
              <span>CareerPilot</span>
            </Link>
            <div className="hidden md:flex ml-10 space-x-8">
              <Link
                to="/dashboard"
                className="text-slate-600 hover:text-slate-900 inline-flex items-center px-1 pt-1 text-sm font-medium"
              >
                Dashboard
              </Link>
              <Link
                to="/resume"
                className="text-slate-600 hover:text-slate-900 inline-flex items-center px-1 pt-1 text-sm font-medium"
              >
                CV Skills
              </Link>
              <Link
                to="/interviews/new"
                className="text-slate-600 hover:text-slate-900 inline-flex items-center px-1 pt-1 text-sm font-medium"
              >
                Practice
              </Link>
              <Link
                to="/mastery"
                className="text-slate-600 hover:text-slate-900 inline-flex items-center px-1 pt-1 text-sm font-medium"
              >
                Skill Mastery
              </Link>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {user ? (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 text-sm text-slate-700">
                  <UserIcon className="h-4 w-4 text-slate-400" />
                  <span className="font-medium">
                    {user.profile?.full_name || user.email}
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={logout}
                  className="flex items-center gap-1.5"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span>Sign Out</span>
                </Button>
              </div>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-sm font-medium text-slate-700 hover:text-slate-900"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="text-sm font-medium px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
