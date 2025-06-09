// frontend/app/connexion/page.js
'use client';

import { useState, useEffect } from 'react'; // Added useEffect
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext'; // Importer useAuth

export default function ConnexionPage() {
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();
  const { login, user, loading } = useAuth(); // Utiliser le contexte d'authentification, get user and loading state

  // Redirect if user is already logged in and not loading
  useEffect(() => {
    if (!loading && user) {
      router.push('/'); // Or a dashboard page
    }
  }, [user, loading, router]);


  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (!login) { // Check if login function is available from context
        setError("Le service d'authentification n'est pas disponible.");
        return;
    }

    try {
      const success = await login(name, password); // Utiliser auth.login
      if (success) {
        router.push('/'); // Rediriger vers la page d'accueil ou un dashboard
      } else {
        // This part might not be reached if login throws an error for all failure cases
        setError('Réponse inattendue du serveur lors de la connexion.');
      }
    } catch (err) {
      console.error('Erreur de connexion sur la page:', err);
      // err.data from fetchApi should contain the JSON error from backend
      // err.message is the primary message from the Error object
      setError(err.data?.detail || err.message || 'Une erreur est survenue lors de la connexion.');
    }
  };

  // Do not render the form if loading and user might be logged in (to avoid flash of login page)
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Chargement...</div>;
  }
  // If after loading, user is found (e.g. from localStorage), useEffect will redirect.
  // So, only show form if no user after loading.
  if (!loading && user) {
    return <div className="min-h-screen flex items-center justify-center">Redirection...</div>; // Or null, or a spinner
  }


  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 shadow-lg rounded-xl">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Connexion Association
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <input type="hidden" name="remember" defaultValue="true" />
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="name" className="sr-only">
                Nom de l&apos;association
              </label>
              <input
                id="name" name="name" type="text" autoComplete="name" required
                value={name} onChange={(e) => setName(e.target.value)}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Nom de l'association"
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">Mot de passe</label>
              <input
                id="password" name="password" type="password" autoComplete="current-password" required
                value={password} onChange={(e) => setPassword(e.target.value)}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Mot de passe"
              />
            </div>
          </div>
          {error && (<div className="text-red-500 text-sm text-center">{error}</div>)}
          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Se connecter
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
