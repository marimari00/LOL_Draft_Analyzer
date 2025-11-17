import React, { useEffect, useMemo, useRef, useState } from 'react';
import './SlotChampionInput.css';

const MAX_SUGGESTIONS = 6;
const normalizeKey = (value = '') => value.toLowerCase().replace(/[^a-z0-9]/g, '');

const SlotChampionInput = ({
  slot,
  team,
  champions = [],
  isActive,
  disabled,
  onSubmit
}) => {
  const [value, setValue] = useState('');
  const [status, setStatus] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isActive && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
    if (!isActive) {
      setValue('');
    }
  }, [isActive, slot?.id]);

  useEffect(() => {
    if (status?.type !== 'success') return undefined;
    const timer = setTimeout(() => setStatus(null), 2000);
    return () => clearTimeout(timer);
  }, [status]);

  const suggestions = useMemo(() => {
    if (!champions.length) return [];
    const term = value.trim().toLowerCase();
    const normalizedTerm = normalizeKey(value);
    const preferredRole = slot?.role || null;
    const scored = champions.map(champion => {
      let priority = 1;
      const normalizedName = normalizeKey(champion.name);
      const roleMatch = preferredRole && champion.roles.includes(preferredRole);
      if (roleMatch) {
        priority -= 0.6;
      }
      if (term) {
        if (champion.name.toLowerCase().startsWith(term)) {
          priority -= 0.5;
        } else if (normalizedName.startsWith(normalizedTerm)) {
          priority -= 0.4;
        } else if (champion.name.toLowerCase().includes(term)) {
          priority -= 0.2;
        }
      }
      return { champion, priority };
    });
    return scored
      .sort((a, b) => {
        if (a.priority !== b.priority) {
          return a.priority - b.priority;
        }
        return a.champion.name.localeCompare(b.champion.name);
      })
      .slice(0, MAX_SUGGESTIONS)
      .map(entry => entry.champion);
  }, [champions, value, slot]);

  const submitValue = async (rawInput) => {
    if (!onSubmit) return;
    const payload = rawInput || value;
    if (!payload || !payload.trim()) {
      setStatus({ type: 'error', message: 'Type a champion name' });
      return;
    }
    setSubmitting(true);
    try {
      const result = await Promise.resolve(onSubmit(payload.trim()));
      if (result?.success) {
        setStatus({ type: 'success', message: `${result.champion || payload} locked` });
        setValue('');
      } else {
        setStatus({ type: 'error', message: result?.message || 'Unable to lock pick' });
      }
      return result;
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmit = () => {
    submitValue(value);
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleSubmit();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      setValue('');
      setStatus(null);
    }
  };

  const placeholder = disabled
    ? 'Waiting for turn'
    : `Type champion for ${slot?.role || 'FLEX'}`;

  return (
    <div className={`slot-entry ${isActive ? 'active' : ''} ${disabled ? 'disabled' : ''}`}>
      <div className="slot-entry-input-row">
        <input
          ref={inputRef}
          type="text"
          className="slot-entry-input"
          placeholder={placeholder}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            if (status) {
              setStatus(null);
            }
          }}
          onKeyDown={handleKeyDown}
          disabled={disabled || submitting}
          aria-label={`Enter champion for ${slot?.id}`}
        />
        <button
          type="button"
          className="slot-entry-confirm"
          onClick={handleSubmit}
          disabled={disabled || submitting}
        >
          ↵
        </button>
      </div>
      {status && (
        <div className={`slot-entry-status ${status.type}`}>
          {status.message}
        </div>
      )}
      <div className="slot-entry-hints">
        {suggestions.map(champion => (
          <button
            key={champion.name}
            type="button"
            className="slot-entry-chip"
            onClick={() => submitValue(champion.name)}
            disabled={disabled || submitting}
          >
            {champion.name}
          </button>
        ))}
      </div>
      {!suggestions.length && (
        <div className="slot-entry-hints muted">
          {team === 'blue' ? 'Blue' : 'Red'} slot • {slot?.role || 'Flex'}
        </div>
      )}
    </div>
  );
};

export default SlotChampionInput;
