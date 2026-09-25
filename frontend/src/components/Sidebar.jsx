export function Sidebar({
  games,
  selectedGameId,
  onSelectGame,
  onAddGame,
  isLoading,
}) {
  return (
    <aside className="sidebar">
      <div className="brand-mark" aria-hidden="true">
        BM
      </div>
      <div className="brand-copy">
        <span className="eyebrow">Rules intelligence</span>
        <h1>BoardMind</h1>
      </div>

      <div className="sidebar-heading">
        <span>Your library</span>
        <span className="count-badge">{games.length}</span>
      </div>

      <nav className="game-list" aria-label="Games">
        {isLoading && <p className="muted-message">Loading library...</p>}
        {!isLoading && games.length === 0 && (
          <p className="muted-message">Your first rulebook belongs here.</p>
        )}
        {!isLoading &&
          games.map((game) => (
            <button
              className={`game-item ${selectedGameId === game.id ? 'is-selected' : ''}`}
              key={game.id}
              onClick={() => onSelectGame(game)}
              type="button"
            >
              <span className="game-icon">
                {game.title.slice(0, 1).toUpperCase()}
              </span>
              <span className="game-name">{game.title}</span>
              <span className="chevron" aria-hidden="true">
                ›
              </span>
            </button>
          ))}
      </nav>

      <button className="add-game-button" onClick={onAddGame} type="button">
        <span aria-hidden="true">+</span>
        Add game &amp; rules
      </button>

      <div className="sidebar-footer">
        <span className="status-dot" aria-hidden="true" />
        <span>Workspace ready</span>
      </div>
    </aside>
  );
}
