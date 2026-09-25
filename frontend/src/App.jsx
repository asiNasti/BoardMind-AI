import { useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { UploadModal } from './components/UploadModal';
import { createGame, listGames, uploadDocument } from './services/api';
import './styles.css';

function App() {
  const [games, setGames] = useState([]);
  const [selectedGame, setSelectedGame] = useState(null);
  const [isLoadingGames, setIsLoadingGames] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    listGames()
      .then((loadedGames) => {
        setGames(loadedGames);
        setSelectedGame(loadedGames[0] ?? null);
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setIsLoadingGames(false));
  }, []);

  const handleAddGame = async ({ title, description, file }) => {
    setIsUploading(true);
    setError('');
    try {
      const game = await createGame({
        title,
        description: description || null,
      });
      await uploadDocument(game.id, file);
      setGames((currentGames) => [...currentGames, game]);
      setSelectedGame(game);
      setIsModalOpen(false);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="app-shell">
      <Sidebar
        games={games}
        isLoading={isLoadingGames}
        onAddGame={() => {
          setError('');
          setIsModalOpen(true);
        }}
        onSelectGame={setSelectedGame}
        selectedGameId={selectedGame?.id}
      />
      <main className="main-content">
        <header className="topbar">
          <span className="breadcrumb">
            Library <span>/</span> {selectedGame?.title ?? 'Overview'}
          </span>
          <span className="account-chip">Guest workspace</span>
        </header>
        <section className="welcome-panel">
          <div className="panel-copy">
            <span className="eyebrow">Your rules desk</span>
            <h2>
              {selectedGame ? selectedGame.title : 'Make every rule clear.'}
            </h2>
            <p>
              {selectedGame
                ? 'Your rulebook is ready for questions. Chat support is coming next.'
                : 'Upload a board game rulebook to build your searchable library.'}
            </p>
            {!selectedGame && (
              <button
                className="primary-button"
                onClick={() => setIsModalOpen(true)}
                type="button"
              >
                Add your first game <span aria-hidden="true">↗</span>
              </button>
            )}
          </div>
          <div className="panel-illustration" aria-hidden="true">
            <span>RULES</span>
            <strong>01</strong>
          </div>
        </section>
        {error && !isModalOpen && (
          <p className="page-error" role="alert">
            {error}
          </p>
        )}
      </main>
      <UploadModal
        error={error}
        isLoading={isUploading}
        isOpen={isModalOpen}
        onClose={() => !isUploading && setIsModalOpen(false)}
        onSubmit={handleAddGame}
      />
    </div>
  );
}

export default App;
