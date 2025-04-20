'use client';

import { useState } from 'react';

interface SearchProps {
  onSearch: (params: { area: string; maxPrice: string; broker: string }) => void;
  brokers: string[];
}

export function PropertySearch({ onSearch, brokers }: SearchProps) {
  const [area, setArea] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [broker, setBroker] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({ area, maxPrice, broker });
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-sm">
      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="md:col-span-1">
          <input
            type="text"
            placeholder="Location (e.g., Utrecht)"
            value={area}
            onChange={(e) => setArea(e.target.value)}
            className="w-full px-4 py-2 border rounded-md"
          />
        </div>
        <div className="md:col-span-1">
          <select
            value={broker}
            onChange={(e) => setBroker(e.target.value)}
            className="w-full px-4 py-2 border rounded-md"
          >
            <option value="">All Brokers</option>
            {brokers.map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
        </div>
        <div className="md:col-span-1">
          <input
            type="number"
            placeholder="Max Price"
            value={maxPrice}
            onChange={(e) => setMaxPrice(e.target.value)}
            className="w-full px-4 py-2 border rounded-md"
          />
        </div>
        <div className="md:col-span-1">
          <button
            type="submit"
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Search
          </button>
        </div>
      </form>
    </div>
  );
}