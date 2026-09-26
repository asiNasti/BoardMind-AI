import { useEffect, useRef, useState } from 'react';
import {
  createChatSession,
  listChatMessages,
  sendChatMessage,
} from '../services/api';
import { MarkdownView } from './MarkdownView';

export function ChatWindow({ game }) {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState('');
  const sessions = useRef(new Map());
  const sessionRequests = useRef(new Map());
  const messagesEndRef = useRef(null);

  useEffect(() => {
    let isCurrent = true;
    const loadChat = async () => {
      setIsLoading(true);
      setError('');
      setMessages([]);
      try {
        let currentSessionId = sessions.current.get(game.id);
        if (!currentSessionId) {
          let sessionRequest = sessionRequests.current.get(game.id);
          if (!sessionRequest) {
            sessionRequest = createChatSession(game.id).then((session) => {
              sessions.current.set(game.id, session.id);
              return session.id;
            });
            sessionRequests.current.set(game.id, sessionRequest);
          }
          currentSessionId = await sessionRequest;
        }
        const history = await listChatMessages(currentSessionId);
        if (isCurrent) {
          setSessionId(currentSessionId);
          setMessages(history);
        }
      } catch (requestError) {
        if (isCurrent) setError(requestError.message);
      } finally {
        if (isCurrent) setIsLoading(false);
      }
    };

    loadChat();
    return () => {
      isCurrent = false;
    };
  }, [game.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const content = draft.trim();
    if (!content || !sessionId || isSending) return;

    setDraft('');
    setError('');
    setMessages((currentMessages) => [
      ...currentMessages,
      { id: `pending-${Date.now()}`, role: 'user', content },
    ]);
    setIsSending(true);
    try {
      const response = await sendChatMessage(sessionId, content);
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `answer-${Date.now()}`,
          role: 'assistant',
          content: response.content,
        },
      ]);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <section className="chat-window" aria-labelledby="chat-title">
      <header className="chat-header">
        <div>
          <span className="eyebrow">Rules desk</span>
          <h2 id="chat-title">Ask about {game.title}</h2>
        </div>
        <span className="chat-status">Grounded in your rulebook</span>
      </header>
      <div className="message-list" aria-live="polite">
        {isLoading && (
          <p className="chat-placeholder">Opening your rules desk...</p>
        )}
        {!isLoading && messages.length === 0 && (
          <div className="chat-placeholder">
            <strong>What would you like to clarify?</strong>
            <p>Ask about setup, turn order, scoring, or a specific card.</p>
          </div>
        )}
        {messages.map((message) => (
          <article className={`message ${message.role}`} key={message.id}>
            <span className="message-label">
              {message.role === 'user' ? 'You' : 'BoardMind'}
            </span>
            {message.role === 'assistant' ? (
              <MarkdownView content={message.content} />
            ) : (
              <p>{message.content}</p>
            )}
          </article>
        ))}
        {isSending && (
          <p className="chat-placeholder">
            BoardMind is checking the rulebook...
          </p>
        )}
        <div ref={messagesEndRef} />
      </div>
      {error && (
        <p className="chat-error" role="alert">
          {error}
        </p>
      )}
      <form className="chat-composer" onSubmit={handleSubmit}>
        <label className="visually-hidden" htmlFor="chat-question">
          Ask a rules question
        </label>
        <textarea
          disabled={isLoading || isSending}
          id="chat-question"
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              event.currentTarget.form.requestSubmit();
            }
          }}
          placeholder="Ask a question about the rules..."
          rows="2"
          value={draft}
        />
        <button
          disabled={!draft.trim() || isLoading || isSending}
          type="submit"
        >
          <span aria-hidden="true">↗</span>
          Send
        </button>
      </form>
    </section>
  );
}
