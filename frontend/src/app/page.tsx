'use client';

import { useState } from 'react';
import { PropertySearch } from '@/components/PropertyScearch';
import { PropertyCard } from '@/components/PropertyCard';

interface Property {
  address: string;
  price: string;
  area: string;
  bedrooms: string;
  energy_label?: string;
  furnished: boolean;
  including_bills: boolean;
  status: string;
  available_from: string;
  url: string;
}

export default function Home() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async ({ area, maxPrice, broker }: { area: string; maxPrice: string; broker: string }) => {
    try {
      setLoading(true);
      setError('');
      
      const params = new URLSearchParams();
      if (area) params.append('address', area);
      if (maxPrice) params.append('max_price', maxPrice);
      if (broker) params.append('broker', broker);
      
      const response = await fetch(`http://localhost:8000/properties?${params}`);
      if (!response.ok) throw new Error('Failed to fetch properties');
      
      const data = await response.json();
      setProperties(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-20">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl font-bold mb-6 text-center">
            Find Your Next Home
          </h1>
          <p className="text-xl mb-8 text-center">
            Rent a place, stay for months
          </p>
          <PropertySearch
            onSearch={handleSearch}
            brokers={['YourHouse', 'OtherBroker']} // Add your broker names here
          />
        </div>
      </div>

      {/* Results Section */}
      <div className="container mx-auto px-4 py-12">
        {loading && (
          <div className="text-center">Loading...</div>
        )}
        
        {error && (
          <div className="text-red-600 text-center mb-4">{error}</div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {properties.map((property, index) => (
            <PropertyCard key={index} {...property} />
          ))}
        </div>

        {!loading && !error && properties.length === 0 && (
          <div className="text-center text-gray-600">
            No properties found. Try adjusting your search criteria.
          </div>
        )}
      </div>
    </div>
  );
}
