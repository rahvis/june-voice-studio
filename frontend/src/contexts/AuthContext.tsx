'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { PublicClientApplication, AuthenticationResult, AccountInfo, SilentRequest } from '@azure/msal-browser';
import { MsalProvider, useMsal } from '@azure/msal-react';

// MSAL configuration
const msalConfig = {
  auth: {
    clientId: process.env.NEXT_PUBLIC_AZURE_CLIENT_ID || '',
    authority: `https://login.microsoftonline.com/${process.env.NEXT_PUBLIC_AZURE_TENANT_ID || ''}`,
    redirectUri: process.env.NEXT_PUBLIC_REDIRECT_URI || 'http://localhost:3000',
    postLogoutRedirectUri: process.env.NEXT_PUBLIC_POST_LOGOUT_REDIRECT_URI || 'http://localhost:3000',
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
  system: {
    allowNativeBroker: false,
    loggerOptions: {
      loggerCallback: (level: any, message: string, containsPii: boolean) => {
        if (containsPii) {
          return;
        }
        switch (level) {
          case 0:
            console.error(message);
            return;
          case 1:
            console.warn(message);
            return;
          case 2:
            console.info(message);
            return;
          case 3:
            console.debug(message);
            return;
          default:
            console.log(message);
            return;
        }
      },
      logLevel: 3,
    },
  },
};

// Scopes for API access
const loginRequest = {
  scopes: ['User.Read', 'openid', 'profile', 'email'],
};

// API scopes
const apiRequest = {
  scopes: [`api://${process.env.NEXT_PUBLIC_AZURE_CLIENT_ID}/access_as_user`],
};

// User roles
export enum UserRole {
  USER = 'user',
  ADMIN = 'admin',
  MODERATOR = 'moderator',
  PREMIUM = 'premium',
}

// User profile interface
export interface UserProfile {
  id: string;
  displayName: string;
  email: string;
  roles: UserRole[];
  tenantId: string;
  objectId: string;
  isAuthenticated: boolean;
  accessToken?: string;
  idToken?: string;
}

// Authentication context interface
interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  getAccessToken: () => Promise<string | null>;
  hasRole: (role: UserRole) => boolean;
  hasAnyRole: (roles: UserRole[]) => boolean;
  refreshToken: () => Promise<void>;
}

// Create MSAL instance
const msalInstance = new PublicClientApplication(msalConfig);

// Create authentication context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Authentication provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  return (
    <MsalProvider instance={msalInstance}>
      <AuthContextProvider>{children}</AuthContextProvider>
    </MsalProvider>
  );
}

// Main authentication context provider
function AuthContextProvider({ children }: { children: ReactNode }) {
  const { instance, accounts, inProgress } = useMsal();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize authentication state
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        if (accounts.length > 0) {
          const account = accounts[0];
          await handleAccountChange(account);
        }
      } catch (error) {
        console.error('Authentication initialization failed:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, [accounts]);

  // Handle account changes
  const handleAccountChange = async (account: AccountInfo) => {
    try {
      // Get user profile from Microsoft Graph
      const profile = await getUserProfile(account);
      setUser(profile);
    } catch (error) {
      console.error('Failed to get user profile:', error);
      setUser(null);
    }
  };

  // Get user profile from Microsoft Graph
  const getUserProfile = async (account: AccountInfo): Promise<UserProfile> => {
    try {
      // Get access token for Microsoft Graph
      const graphTokenResponse = await instance.acquireTokenSilent({
        ...loginRequest,
        account: account,
      });

      // Get user profile from Microsoft Graph
      const graphResponse = await fetch('https://graph.microsoft.com/v1.0/me', {
        headers: {
          Authorization: `Bearer ${graphTokenResponse.accessToken}`,
        },
      });

      if (!graphResponse.ok) {
        throw new Error('Failed to fetch user profile');
      }

      const graphData = await graphResponse.json();

      // Get user roles from your custom API
      const roles = await getUserRoles(graphTokenResponse.accessToken);

      return {
        id: graphData.id,
        displayName: graphData.displayName,
        email: graphData.mail || graphData.userPrincipalName,
        roles: roles,
        tenantId: account.tenantId,
        objectId: account.localAccountId,
        isAuthenticated: true,
        accessToken: graphTokenResponse.accessToken,
        idToken: graphTokenResponse.idToken,
      };
    } catch (error) {
      console.error('Failed to get user profile:', error);
      throw error;
    }
  };

  // Get user roles from custom API
  const getUserRoles = async (accessToken: string): Promise<UserRole[]> => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/roles`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        return data.roles || [UserRole.USER];
      }

      return [UserRole.USER];
    } catch (error) {
      console.error('Failed to get user roles:', error);
      return [UserRole.USER];
    }
  };

  // Login function
  const login = async (): Promise<void> => {
    try {
      setIsLoading(true);
      await instance.loginPopup(loginRequest);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // Logout function
  const logout = async (): Promise<void> => {
    try {
      setIsLoading(true);
      await instance.logoutPopup({
        postLogoutRedirectUri: process.env.NEXT_PUBLIC_POST_LOGOUT_REDIRECT_URI,
      });
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // Get access token for API calls
  const getAccessToken = async (): Promise<string | null> => {
    try {
      if (!user || !user.isAuthenticated) {
        return null;
      }

      const account = instance.getActiveAccount();
      if (!account) {
        return null;
      }

      const tokenResponse = await instance.acquireTokenSilent({
        ...apiRequest,
        account: account,
      });

      return tokenResponse.accessToken;
    } catch (error) {
      console.error('Failed to get access token:', error);
      return null;
    }
  };

  // Check if user has specific role
  const hasRole = (role: UserRole): boolean => {
    return user?.roles.includes(role) || false;
  };

  // Check if user has any of the specified roles
  const hasAnyRole = (roles: UserRole[]): boolean => {
    return user?.roles.some(role => roles.includes(role)) || false;
  };

  // Refresh token
  const refreshToken = async (): Promise<void> => {
    try {
      if (!user) {
        return;
      }

      const account = instance.getActiveAccount();
      if (!account) {
        return;
      }

      await instance.acquireTokenSilent({
        ...apiRequest,
        account: account,
      });

      // Update user profile
      await handleAccountChange(account);
    } catch (error) {
      console.error('Token refresh failed:', error);
      // If refresh fails, redirect to login
      await logout();
    }
  };

  // Context value
  const contextValue: AuthContextType = {
    user,
    isAuthenticated: !!user?.isAuthenticated,
    isLoading: isLoading || inProgress !== 'none',
    login,
    logout,
    getAccessToken,
    hasRole,
    hasAnyRole,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook to use authentication context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Hook to check if user has specific role
export function useHasRole(role: UserRole): boolean {
  const { hasRole } = useAuth();
  return hasRole(role);
}

// Hook to check if user has any of the specified roles
export function useHasAnyRole(roles: UserRole[]): boolean {
  const { hasAnyRole } = useAuth();
  return hasAnyRole(roles);
}

// Hook to get access token
export function useAccessToken(): () => Promise<string | null> {
  const { getAccessToken } = useAuth();
  return getAccessToken;
}

// Protected route component
export function ProtectedRoute({ 
  children, 
  requiredRoles, 
  fallback 
}: { 
  children: ReactNode;
  requiredRoles?: UserRole[];
  fallback?: ReactNode;
}) {
  const { isAuthenticated, isLoading, hasAnyRole } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="loading-spinner w-8 h-8"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return fallback || (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Authentication Required
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Please log in to access this page.
          </p>
          <button
            onClick={() => window.location.href = '/login'}
            className="btn-primary"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  if (requiredRoles && requiredRoles.length > 0 && !hasAnyRole(requiredRoles)) {
    return fallback || (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Access Denied
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            You don't have permission to access this page.
          </p>
          <button
            onClick={() => window.history.back()}
            className="btn-secondary"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

// Role-based component wrapper
export function RoleBasedComponent({ 
  children, 
  requiredRoles, 
  fallback 
}: { 
  children: ReactNode;
  requiredRoles: UserRole[];
  fallback?: ReactNode;
}) {
  const { hasAnyRole } = useAuth();

  if (!hasAnyRole(requiredRoles)) {
    return fallback || null;
  }

  return <>{children}</>;
}
