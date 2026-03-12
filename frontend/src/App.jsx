import { useState } from 'react'
import './App.css'

function App() {
  // Nos variables d'état (ce que l'utilisateur choisit)
  const [nbJoueurs, setNbJoueurs] = useState(4)
  const [presenceEnnemis, setPresenceEnnemis] = useState(true)
  const [nbEnnemis, setNbEnnemis] = useState(2)
  const [activerAwacs, setActiverAwacs] = useState(true)
  const [activerSam, setActiverSam] = useState(true)
  
  // Pour afficher un petit message "Chargement..."
  const [isLoading, setIsLoading] = useState(false)

  // La fonction qui s'active quand on clique sur "Générer"
  const handleGenerate = async (e) => {
    e.preventDefault()
    setIsLoading(true)

    // On prépare le JSON exact que ton API attend
    const configMission = {
      nb_joueurs: parseInt(nbJoueurs),
      presence_ennemis: presenceEnnemis,
      nb_ennemis: parseInt(nbEnnemis),
      activer_awacs: activerAwacs,
      activer_sam: activerSam
    }

    try {
      // On tape sur ton API Python locale !
      const response = await fetch('http://127.0.0.1:8000/generer-mission', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configMission)
      })

      if (!response.ok) throw new Error("Erreur lors de la génération")

      // --- MAGIE DU TÉLÉCHARGEMENT EN JS ---
      // On récupère le fichier binaire (.miz)
      const blob = await response.blob()
      // On crée un faux lien invisible
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = "Black_Sea_Iron_Storm.miz" // Le nom du fichier qui va se télécharger
      document.body.appendChild(a)
      a.click() // On clique dessus automatiquement
      window.URL.revokeObjectURL(url) // On nettoie
      
    } catch (error) {
      alert("Aïe, l'API a planté : " + error.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="App" style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Générateur de Mission DCS ✈️</h1>
      <p>Configure ta mission Iron Storm sur mesure.</p>

      <form onSubmit={handleGenerate} style={{ display: 'flex', flexDirection: 'column', gap: '15px', maxWidth: '400px', margin: '0 auto' }}>
        
        <label>
          Nombre de joueurs (F-15C) : {nbJoueurs}
          <input type="range" min="1" max="16" value={nbJoueurs} onChange={e => setNbJoueurs(e.target.value)} />
        </label>

        <label>
          <input type="checkbox" checked={presenceEnnemis} onChange={e => setPresenceEnnemis(e.target.checked)} />
          Activer les ennemis (Su-27)
        </label>

        {presenceEnnemis && (
          <label>
            Nombre d'ennemis : {nbEnnemis}
            <input type="range" min="1" max="16" value={nbEnnemis} onChange={e => setNbEnnemis(e.target.value)} />
          </label>
        )}

        <label>
          <input type="checkbox" checked={activerAwacs} onChange={e => setActiverAwacs(e.target.checked)} />
          Soutien AWACS
        </label>

        <label>
          <input type="checkbox" checked={activerSam} onChange={e => setActiverSam(e.target.checked)} />
          Défenses SAM sur les bases
        </label>

        <button type="submit" disabled={isLoading} style={{ padding: '10px', fontSize: '1.2rem', cursor: 'pointer', marginTop: '10px' }}>
          {isLoading ? "Génération en cours..." : "🚀 Générer la mission"}
        </button>
      </form>
    </div>
  )
}

export default App