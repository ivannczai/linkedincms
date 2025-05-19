import React, { useState, useEffect, useMemo } from 'react'; // Added useMemo
import { useNavigate, useSearchParams } from 'react-router-dom';
import contentService, {
	Content,
	ContentStatus,
	ContentSortField,
	SortOrder,
} from '../../services/contents'; // Import sort types
import { useAuth } from '../../context/AuthContext';
import ContentCard from '../../components/contents/ContentCard';
import { ListFilter } from 'lucide-react'; // Icon for sorting dropdown

// Define sorting options
const sortOptions: {
	label: string;
	value: ContentSortField;
	orders: SortOrder[];
}[] = [
	{ label: 'Creation Date', value: 'created_at', orders: ['desc', 'asc'] },
	{ label: 'Due Date', value: 'due_date', orders: ['asc', 'desc'] },
	{ label: 'Last Updated', value: 'updated_at', orders: ['desc', 'asc'] },
	{ label: 'Title', value: 'title', orders: ['asc', 'desc'] },
];

const ClientContentLibraryPage: React.FC = () => {
	const [searchParams, setSearchParams] = useSearchParams();
	const { user } = useAuth();
	const navigate = useNavigate();

	const [contents, setContents] = useState<Content[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	// Read filters and sorting from URL search params
	const statusFilter = (searchParams.get('status') || '') as ContentStatus | '';
	const sortBy = (searchParams.get('sort_by') ||
		'created_at') as ContentSortField; // Default sort
	const sortOrder = (searchParams.get('sort_order') || 'desc') as SortOrder; // Default order

	// Fetch content based on filter and sort
	useEffect(() => {
		const fetchClientContents = async () => {
			if (!user?.client_id) return;
			try {
				setLoading(true);
				setError(null);
				const data = await contentService.getAll(
					user.client_id,
					statusFilter === '' ? undefined : statusFilter,
					sortBy, // Pass sorting parameters
					sortOrder
				);
				// Filter out DRAFT content on the frontend
				const filteredData = data.filter(
					(c) => c.status !== ContentStatus.DRAFT
				);
				setContents(filteredData);
			} catch (err) {
				console.error('Failed to fetch client contents:', err);
				setError('Failed to load content pieces.');
			} finally {
				setLoading(false);
			}
		};

		fetchClientContents();
	}, [user?.client_id, statusFilter, sortBy, sortOrder]); // Re-fetch when filter or sort changes

	// Update URL search params for filters and sorting
	const updateSearchParams = (newParams: Record<string, string>) => {
		const currentParams = Object.fromEntries(searchParams.entries());
		setSearchParams({ ...currentParams, ...newParams });
	};

	const handleStatusFilterClick = (newStatus: ContentStatus | '') => {
		updateSearchParams(newStatus ? { status: newStatus } : { status: '' });
		// Reset sort? Optional, maybe keep current sort when changing filter
	};

	const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
		const [newSortBy, newSortOrder] = e.target.value.split(':');
		updateSearchParams({ sort_by: newSortBy, sort_order: newSortOrder });
	};

	const getPageTitle = () => {
		if (statusFilter === ContentStatus.PENDING_APPROVAL)
			return 'Content Pending Approval';
		if (statusFilter === ContentStatus.REVISION_REQUESTED)
			return 'Content Needing Revision';
		if (statusFilter === ContentStatus.APPROVED) return 'Approved Content';
		if (statusFilter === ContentStatus.PUBLISHED) return 'Published Content';
		return 'Content Library';
	};

	// Handler for the Mark as Posted action from the card
	const handleMarkAsPosted = async (id: number) => {
		navigate(`/dashboard/linkedin/schedule?id=${id}`);
	};

	if (!user?.client_id) {
		return (
			<div className='p-8 text-red-500'>Client information not found.</div>
		);
	}

	// Define statuses relevant to the client
	const clientVisibleStatuses = Object.values(ContentStatus).filter(
		(status) => status !== ContentStatus.DRAFT
	);

	// Memoize the current sort value string for the select input
	const currentSortValue = useMemo(
		() => `${sortBy}:${sortOrder}`,
		[sortBy, sortOrder]
	);

	return (
		<div className='container mx-auto px-4 py-8'>
			<div className='flex justify-between items-center mb-6 flex-wrap gap-4'>
				<h1 className='text-2xl font-bold text-brand-foreground'>
					{getPageTitle()}
				</h1>
				{/* Sorting Dropdown */}
				<div className='flex items-center gap-2'>
					<ListFilter className='w-4 h-4 text-gray-500' />
					<label htmlFor='sort-select' className='sr-only'>
						Sort by:
					</label>
					<select
						id='sort-select'
						value={currentSortValue}
						onChange={handleSortChange}
						className='form-select text-sm rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
					>
						{sortOptions.map((option) =>
							option.orders.map((order) => (
								<option
									key={`${option.value}:${order}`}
									value={`${option.value}:${order}`}
								>
									{option.label} ({order === 'asc' ? 'Asc' : 'Desc'})
								</option>
							))
						)}
					</select>
				</div>
				{/* TODO: Add Search Bar here */}
			</div>

			{/* Status Filter Buttons */}
			<div className='mb-6 flex flex-wrap gap-2 border-b border-gray-200 pb-3'>
				<button
					onClick={() => handleStatusFilterClick('')}
					className={`px-3 py-1.5 rounded-md text-sm font-medium ${statusFilter === '' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
				>
					All
				</button>
				{/* Map only over client-visible statuses */}
				{clientVisibleStatuses.map((statusValue) => (
					<button
						key={statusValue}
						onClick={() => handleStatusFilterClick(statusValue)}
						className={`px-3 py-1.5 rounded-md text-sm font-medium ${statusFilter === statusValue ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
					>
						{statusValue.replace('_', ' ')}
					</button>
				))}
			</div>

			{/* Content Grid */}
			{loading && (
				<div className='flex justify-center items-center p-8'>
					<div className='animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600'></div>
				</div>
			)}
			{error && (
				<div className='m-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded'>
					{error}
				</div>
			)}
			{!loading && !error && contents.length === 0 && (
				<div className='text-center py-12'>
					<p className='text-gray-500'>
						No content pieces found matching the current filter.
					</p>
				</div>
			)}
			{!loading && !error && contents.length > 0 && (
				<div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'>
					{contents.map((content) => (
						<ContentCard
							key={content.id}
							content={content}
							basePath='/client'
							onMarkAsPosted={handleMarkAsPosted} // Pass handler
						/>
					))}
				</div>
			)}
		</div>
	);
};

export default ClientContentLibraryPage;
