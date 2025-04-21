interface PropertyCardProps {
    address: string;
    price: string;
    area: string;
    bedrooms: string;
    status: string;
    energy_label?: string;
    furnished: boolean;
    available_from: string;
    url: string;
  }
  
  export function PropertyCard({
    address,
    price,
    area,
    bedrooms,
    status,
    energy_label,
    furnished,
    available_from,
    url,
  }: PropertyCardProps) {
    return (
      <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-4 border border-gray-100">
        <div className="aspect-w-16 aspect-h-9 mb-4 bg-[var(--secondary)] rounded-md" />
        <h3 className="font-semibold text-lg mb-2 text-[var(--text)]">{address}</h3>
        <p className="text-[var(--primary)] text-xl mb-2">€{price} per month</p>
        <div className="flex justify-between mb-2">
          <span className="text-sm text-gray-600">{area}m² • {bedrooms} bed</span>
          <span className={`px-2 py-1 rounded-full text-xs ${
            status === 'available' 
              ? 'bg-green-100 text-green-800' 
              : 'bg-yellow-100 text-yellow-800'
          }`}>
            {status}
          </span>
        </div>
        <div className="space-y-1 text-sm text-gray-600">
          <div>Available from: {available_from}</div>
          <div>Energy Label: {energy_label || 'N/A'}</div>
          <div>{furnished ? 'Furnished' : 'Unfurnished'}</div>
        </div>
        <a 
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-block px-4 py-2 bg-[var(--primary)] text-white rounded hover:bg-[var(--primary)]/90 text-sm transition-colors"
        >
          View Details
        </a>
      </div>
    );
  }