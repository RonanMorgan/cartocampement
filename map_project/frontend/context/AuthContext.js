// frontend/context/AuthContext.js
'use client';

import { createContext, useContext, useState, useEffect } from 'react';
import { fetchApi } from '@/lib/api'; // Pour un éventuel appel /users/me
import { useRouter, usePathname } from 'next/navigation'; // Added usePathname

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null); // Stores user info like { name: '...', token: '...' } or just token
  const [authToken, setAuthToken] = useState(null); // Explicitly store token
  const [loading, setLoading] = useState(true); // For managing initial token loading & user details fetching
  const router = useRouter();
  const pathname = usePathname(); // To know current path for redirects

  // Function to fetch user details if a token exists
  const fetchUserDetails = async (token) => {
    if (!token) {
        setUser(null);
        setAuthToken(null);
        setLoading(false);
        return;
    }
    try {
      // Assuming /users/me returns user details like name, id, etc.
      const userData = await fetchApi('/users/me', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(userData); // Store full user details
      setAuthToken(token); // Store token
    } catch (error) {
      console.error("Failed to fetch user details with token, logging out:", error);
      localStorage.removeItem('authToken'); // Clear invalid token
      setUser(null);
      setAuthToken(null);
      // Optionally redirect if on a protected page:
      // if (pathname !== '/connexion' && pathname !== '/creer-compte') { // Example protected condition
      //    router.push('/connexion');
      // }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      fetchUserDetails(storedToken);
    } else {
      setLoading(false); // No token, not loading user
    }
  }, []);


  const login = async (name, password) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('username', name);
      params.append('password', password);

      const data = await fetchApi('/auth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params,
      });

      if (data && data.access_token) {
        localStorage.setItem('authToken', data.access_token);
        await fetchUserDetails(data.access_token); // Fetch user details after login
        setLoading(false);
        return true; // Succès
      }
      setLoading(false);
      return false;
    } catch (error) {
      setLoading(false);
      console.error('Login failed in AuthContext', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setUser(null);
    setAuthToken(null);
    // Redirect to login, but ensure it's not causing a loop if already there or if public page
    if (pathname !== '/connexion') {
        router.push('/connexion');
    }
  };

  return (
    <AuthContext.Provider value={{ user, authToken, login, logout, loading, setLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) { // Check for undefined, not null, as initial context value is null
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
