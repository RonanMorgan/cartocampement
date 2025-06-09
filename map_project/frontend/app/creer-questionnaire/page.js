// frontend/app/creer-questionnaire/page.js
'use client';

import QuestionnaireForm from '@/components/QuestionnaireForm';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function CreerQuestionnairePage() {
  const { user, loading, authToken } = useAuth(); // Get authToken as well for direct check if needed
  const router = useRouter();

  useEffect(() => {
    // If not loading and no user (which implies no valid token processed by AuthContext)
    // OR if there's definitively no token (e.g. after logout and state update)
    if (!loading && !user) {
      router.push('/connexion');
    }
  }, [user, loading, router]);

  if (loading) {
    return <div className="container mx-auto p-4 text-center">Chargement de la session...</div>;
  }

  if (!user) {
    // This state might be briefly visible before redirection, or if redirection fails.
    // AuthContext's loading state should ideally cover the initial check.
    return <div className="container mx-auto p-4 text-center">Vous devez être connecté pour créer un questionnaire. Redirection...</div>;
  }

  // If user is authenticated, render the form
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Créer un nouveau questionnaire</h1>
      <QuestionnaireForm />
    </div>
  );
}
