'use client';

import { useEffect, useState } from 'react';
import Lottie from 'react-lottie';
import { PropertySearch } from '@/components/PropertySearch';
import { PropertyCard } from '@/components/PropertyCard';
import animationData from '@/animations/house-search.json';

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

  const defaultOptions = {
    loop: true,
    autoplay: true,
    animationData: animationData,
    rendererSettings: {
      preserveAspectRatio: 'xMidYMid slice'
    }
  };

  return (
    <div className="min-h-screen bg-[var(--background)]">
      <div className="bg-gradient-to-r from-[var(--primary)] to-[var(--secondary)] py-20">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="md:w-1/2 mb-8 md:mb-0">
              <h1 className="text-4xl font-bold mb-6 text-white">
                Find Your Next Home
              </h1>
              <p className="text-xl mb-8 text-white/90">
                Rent a place, stay for months
              </p>
              <PropertySearch
                onSearch={handleSearch}
                brokers={['YourHouse', 'OtherBroker']}
              />
            </div>
            <div className="md:w-1/2 flex justify-center">
              <div className="w-full max-w-md">
                <Lottie options={defaultOptions} height={400} width={400} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Results Section */}
      <div className="container mx-auto px-4 py-12">
        {loading && (
          <div className="text-center">
            <Lottie 
              options={{ 
                loop: true,
                autoplay: true,
                animationData: animationData 
              }}
              height={200}
              width={200}
            />
          </div>
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
