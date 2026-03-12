import { useState } from 'react'
import './App.css'

function App() {
  const [nbJoueurs, setNbJoueurs] = useState(4)
  const [presenceEnnemis, setPresenceEnnemis] = useState(true)
  const [nbEnnemis, setNbEnnemis] = useState(2)
  const [activerAwacs, setActiverAwacs] = useState(true)
  const [activerSam, setActiverSam] = useState(true)
  const [meteo, setMeteo] = useState('clair')
  const [heure, setHeure] = useState('jour')
  const [theatre, setTheatre] = useState('caucase')
  const [isLoading, setIsLoading] = useState(false)
  const [erreur, setErreur] = useState(null)
  const [succes, setSucces] = useState(false)

  const handleGenerate = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setErreur(null)
    setSucces(false)

    const configMission = {
      nb_joueurs: parseInt(nbJoueurs),
      presence_ennemis: presenceEnnemis,
      nb_ennemis: parseInt(nbEnnemis),
      activer_awacs: activerAwacs,
      activer_sam: activerSam,
      meteo,
      heure,
      theatre,
    }

    try {
      const response = await fetch('/api/generer-mission', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configMission)
      })

      if (!response.ok) {
        const text = await response.text()
        throw new Error(`HTTP ${response.status} – ${text.slice(0, 300)}`)
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = "mission.miz"
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      setSucces(true)

    } catch (error) {
      setErreur(error.message)
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
          Théâtre
          <select value={theatre} onChange={e => setTheatre(e.target.value)} style={{ display: 'block', width: '100%', marginTop: '4px' }}>
            <option value="caucase">Caucase (Kutaisi vs Gudauta)</option>
            <option value="golfe_persique">Golfe Persique (Al Dhafra vs Bandar Abbas)</option>
          </select>
        </label>

        <label>
          Météo
          <select value={meteo} onChange={e => setMeteo(e.target.value)} style={{ display: 'block', width: '100%', marginTop: '4px' }}>
            <option value="clair">☀️ Clair</option>
            <option value="nuageux">☁️ Nuageux</option>
            <option value="orage">⛈️ Orage</option>
          </select>
        </label>

        <label>
          Heure de départ
          <select value={heure} onChange={e => setHeure(e.target.value)} style={{ display: 'block', width: '100%', marginTop: '4px' }}>
            <option value="aube">🌅 Aube (06:00)</option>
            <option value="jour">☀️ Jour (12:00)</option>
            <option value="crepuscule">🌆 Crépuscule (18:00)</option>
            <option value="nuit">🌙 Nuit (02:00)</option>
          </select>
        </label>

        <label>
          Nombre de joueurs (F-15C) : {nbJoueurs}
          <input type="range" min="1" max="16" value={nbJoueurs} onChange={e => setNbJoueurs(e.target.value)} style={{ display: 'block', width: '100%' }} />
        </label>

        <label>
          <input type="checkbox" checked={presenceEnnemis} onChange={e => setPresenceEnnemis(e.target.checked)} />
          {' '}Activer les ennemis (Su-27)
        </label>

        {presenceEnnemis && (
          <label>
            Nombre d'ennemis : {nbEnnemis}
            <input type="range" min="1" max="16" value={nbEnnemis} onChange={e => setNbEnnemis(e.target.value)} style={{ display: 'block', width: '100%' }} />
          </label>
        )}

        <label>
          <input type="checkbox" checked={activerAwacs} onChange={e => setActiverAwacs(e.target.checked)} />
          {' '}Soutien AWACS
        </label>

        <label>
          <input type="checkbox" checked={activerSam} onChange={e => setActiverSam(e.target.checked)} />
          {' '}Défenses SAM sur les bases
        </label>

        <button type="submit" disabled={isLoading} style={{ padding: '10px', fontSize: '1.2rem', cursor: 'pointer', marginTop: '10px' }}>
          {isLoading ? "Génération en cours..." : "🚀 Générer la mission"}
        </button>

        {succes && <p style={{ color: 'green', margin: 0 }}>✅ Mission générée et téléchargée !</p>}
        {erreur && <p style={{ color: 'red', margin: 0, fontSize: '0.85rem' }}>❌ {erreur}</p>}
      </form>
    </div>
  )
}

export default App
