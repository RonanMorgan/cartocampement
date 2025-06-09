// frontend/components/QuestionnaireForm.js
'use client';

import { useState } from 'react';
import { fetchApi } from '@/lib/api'; // Importer fetchApi
import { useRouter } from 'next/navigation';

export default function QuestionnaireForm() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [password, setPassword] = useState('');
  const [elements, setElements] = useState([
    { id: Date.now(), label: '', fieldType: 'text' }
  ]);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const router = useRouter();

  const fieldTypes = [
    { value: 'text', name: 'Texte court' },
    { value: 'number', name: 'Chiffre' },
    { value: 'coordinates_lat', name: 'Coordonnée (Latitude)' },
    { value: 'coordinates_lon', name: 'Coordonnée (Longitude)' },
    { value: 'date', name: 'Date' },
    { value: 'email', name: 'Adresse e-mail' },
  ];

  const addElement = () => {
    setElements([...elements, { id: Date.now(), label: '', fieldType: 'text' }]);
  };

  const removeElement = (id) => {
    setElements(elements.filter(element => element.id !== id));
  };

  const handleElementChange = (id, event) => {
    const { name, value } = event.target;
    setElements(elements.map(element =>
      element.id === id ? { ...element, [name]: value } : element
    ));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccessMessage('');

    if (!title.trim()) {
        setError('Le titre du questionnaire est requis.');
        return;
    }
    if (elements.some(el => !el.label.trim())) {
        setError('Chaque question doit avoir un libellé.');
        return;
    }

    const questionnaireData = {
      title,
      description,
      password: password || null,
      elements: elements.map(({ id, label, fieldType }) => ({ label, field_type: fieldType })), // Exclude client-side id
    };

    try {
      const createdQuestionnaire = await fetchApi('/questionnaires/', {
        method: 'POST',
        body: questionnaireData,
      });
      setSuccessMessage(`Questionnaire "${createdQuestionnaire.title}" créé avec succès !`);
      alert(`Questionnaire créé ! ID: ${createdQuestionnaire.id}. Titre: ${createdQuestionnaire.title}`);

      setTitle('');
      setDescription('');
      setPassword('');
      setElements([{ id: Date.now(), label: '', fieldType: 'text' }]);
      // router.push(`/questionnaires/${createdQuestionnaire.id}`); // Optional redirect
    } catch (err) {
      console.error('Erreur lors de la création du questionnaire:', err);
      setError(err.data?.detail || err.message || 'Une erreur est survenue lors de la création.');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="title" className="block text-sm font-medium text-gray-700">Titre du questionnaire</label>
        <input type="text" name="title" id="title" value={title} onChange={(e) => setTitle(e.target.value)} required className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"/>
      </div>
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700">Description (optionnel)</label>
        <textarea name="description" id="description" value={description} onChange={(e) => setDescription(e.target.value)} rows={3} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"></textarea>
      </div>
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">Mot de passe d&apos;accès au questionnaire (optionnel)</label>
        <input type="password" name="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"/>
      </div>
      <hr/>
      <div className="space-y-4">
        <h3 className="text-lg font-medium leading-6 text-gray-900">Questions du questionnaire</h3>
        {elements.map((element, index) => (
          <div key={element.id} className="p-4 border border-gray-200 rounded-md space-y-3">
            <p className="text-md font-semibold">Question {index + 1}</p>
            <div>
              <label htmlFor={`element-label-${element.id}`} className="block text-sm font-medium text-gray-700">Libellé de la question</label>
              <input type="text" name="label" id={`element-label-${element.id}`} value={element.label} onChange={(e) => handleElementChange(element.id, e)} required className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"/>
            </div>
            <div>
              <label htmlFor={`element-fieldType-${element.id}`} className="block text-sm font-medium text-gray-700">Type de champ</label>
              <select name="fieldType" id={`element-fieldType-${element.id}`} value={element.fieldType} onChange={(e) => handleElementChange(element.id, e)} className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md">
                {fieldTypes.map(type => (<option key={type.value} value={type.value}>{type.name}</option>))}
              </select>
            </div>
            {elements.length > 1 && (<button type="button" onClick={() => removeElement(element.id)} className="text-sm font-medium text-red-600 hover:text-red-500">Supprimer cette question</button>)}
          </div>
        ))}
        <button type="button" onClick={addElement} className="mt-2 py-2 px-4 border border-dashed border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">Ajouter une question</button>
      </div>
      <hr/>
      {error && <p className="text-red-500 text-sm my-2 text-center">{error}</p>}
      {successMessage && <p className="text-green-500 text-sm my-2 text-center">{successMessage}</p>}
      <div>
        <button type="submit" className="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">Créer le questionnaire</button>
      </div>
    </form>
  );
}
