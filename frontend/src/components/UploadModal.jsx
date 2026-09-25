import { useEffect, useRef, useState } from 'react';

export function UploadModal({ isOpen, onClose, onSubmit, isLoading, error }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!isOpen) {
      setTitle('');
      setDescription('');
      setFile(null);
      setFileError('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0] ?? null;

    if (!selectedFile) {
      setFile(null);
      setFileError('');
      return;
    }

    const isPdf =
      selectedFile.type === 'application/pdf' ||
      selectedFile.name.toLowerCase().endsWith('.pdf');

    if (!isPdf) {
      setFile(null);
      setFileError('Please choose a valid PDF rulebook.');
      event.target.value = '';
      return;
    }

    setFile(selectedFile);
    setFileError('');
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!title.trim()) {
      return;
    }

    if (!file) {
      setFileError('Please choose a PDF rulebook before creating the game.');
      return;
    }

    onSubmit({ title: title.trim(), description: description.trim(), file });
  };

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <section
        aria-labelledby="upload-title"
        aria-modal="true"
        className="modal"
        role="dialog"
      >
        <button
          aria-label="Close upload dialog"
          className="close-button"
          onClick={onClose}
          type="button"
        >
          ×
        </button>
        <span className="modal-kicker">New collection</span>
        <h2 id="upload-title">Bring a game to the table.</h2>
        <p className="modal-intro">
          Give your rulebook a home. BoardMind will index it for quick, grounded
          answers.
        </p>
        <form onSubmit={handleSubmit}>
          <label htmlFor="game-title">Game title</label>
          <input
            id="game-title"
            onChange={(event) => setTitle(event.target.value)}
            placeholder="e.g. Wingspan"
            required
            value={title}
          />

          <label htmlFor="game-description">
            Short description <span>(optional)</span>
          </label>
          <textarea
            id="game-description"
            onChange={(event) => setDescription(event.target.value)}
            placeholder="A note for your future self"
            rows="2"
            value={description}
          />

          <label htmlFor="rulebook">Rulebook PDF</label>
          <button
            className={`file-drop ${file ? 'has-file' : ''}`}
            onClick={() => fileInputRef.current?.click()}
            type="button"
          >
            <span className="file-icon" aria-hidden="true">
              ↥
            </span>
            <span>{file ? file.name : 'Choose a PDF rulebook'}</span>
            <span className="file-hint">
              {file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : 'PDF only'}
            </span>
          </button>
          <input
            accept=".pdf,application/pdf"
            className="visually-hidden"
            id="rulebook"
            onChange={handleFileChange}
            ref={fileInputRef}
            type="file"
          />

          {(error || fileError) && (
            <p className="form-error" role="alert">
              {error || fileError}
            </p>
          )}
          <button
            className="submit-button"
            disabled={isLoading || !title.trim() || !file}
            type="submit"
          >
            {isLoading ? (
              <>
                <span className="spinner" aria-hidden="true" /> Indexing
                rulebook...
              </>
            ) : (
              'Create game & upload'
            )}
          </button>
        </form>
      </section>
    </div>
  );
}
