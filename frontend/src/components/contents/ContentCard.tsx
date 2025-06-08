import React from 'react';
import { Link } from 'react-router-dom';
import { Content, ContentStatus } from '../../services/contents';
import { formatDate } from '../../utils/formatters';
import {
	Eye,
	Edit,
	Copy,
	CheckCheck,
	Star,
	AlertTriangle,
	Clock,
} from 'lucide-react'; // Add Star, AlertTriangle, Clock
import { cn } from '../../utils/cn'; // Import cn utility

interface ContentCardProps {
	content: Content;
	basePath: string; // e.g., "/client" or "/admin/clients/:clientId"
	onMarkAsPosted?: (id: number) => Promise<void>; // Optional handler for client action
	onCopy?: (text: string) => void; // Optional handler for copying text
}

const ContentCard: React.FC<ContentCardProps> = ({
	content,
	basePath,
	onMarkAsPosted,
	onCopy,
}) => {
	const getStatusBadgeClass = (status: ContentStatus) => {
		switch (status) {
			case ContentStatus.DRAFT:
				return 'bg-gray-100 text-gray-600';
			case ContentStatus.PENDING_APPROVAL:
				return 'bg-yellow-100 text-yellow-700';
			case ContentStatus.REVISION_REQUESTED:
				return 'bg-red-100 text-red-700';
			case ContentStatus.APPROVED:
				return 'bg-green-100 text-green-700';
			case ContentStatus.SCHEDULED:
				return 'bg-purple-100 text-purple-700';
			case ContentStatus.PUBLISHED:
				return 'bg-blue-100 text-blue-700';
			default:
				return 'bg-gray-100 text-gray-600';
		}
	};

	// Function to get conditional border class for client view
	const getCardBorderClass = (status: ContentStatus) => {
		if (!basePath.startsWith('/client')) return ''; // Only apply for client view
		switch (status) {
			case ContentStatus.PENDING_APPROVAL:
				return 'border-l-4 border-yellow-400';
			case ContentStatus.REVISION_REQUESTED:
				return 'border-l-4 border-red-500';
			case ContentStatus.APPROVED:
				return 'border-l-4 border-green-500';
			default:
				return 'border-l-4 border-transparent'; // Default transparent border
		}
	};

	const handleCopy = () => {
		if (onCopy) {
			onCopy(content.content_body); // Assuming content_body is now HTML, might need text extraction
		} else {
			// Extract text from HTML for clipboard
			const tempDiv = document.createElement('div');
			tempDiv.innerHTML = content.content_body || '';
			const textToCopy = tempDiv.textContent || tempDiv.innerText || '';
			navigator.clipboard
				.writeText(textToCopy)
				.then(() => alert('Content text copied to clipboard!')) // Basic feedback
				.catch((err) => console.error('Failed to copy text: ', err));
		}
	};

	const handleMarkPostedClick = async () => {
		if (onMarkAsPosted) {
			try {
				await onMarkAsPosted(content.id);
				// Optionally show success feedback here if needed
			} catch (error) {
				console.error('Failed to mark as posted:', error);
				// Optionally show error feedback here
			}
		}
	};

	// Determine view/edit link based on basePath
	const viewLink = `${basePath}/contents/${content.id}`;
	// Admin edit link structure might differ, assuming admin path includes client ID
	const editLink = `/admin/clients/${content.client_id}/contents/${content.id}/edit`;

	const isClientView = basePath.startsWith('/client');

	// Extract plain text snippet from HTML content_body
	const getSnippet = (html: string, maxLength: number = 100): string => {
		const tempDiv = document.createElement('div');
		tempDiv.innerHTML = html || '';
		const text = tempDiv.textContent || tempDiv.innerText || '';
		return text.length > maxLength
			? text.substring(0, maxLength) + '...'
			: text;
	};

	return (
		// Use cn utility to merge classes and add conditional border
		<div
			className={cn(
				'card flex flex-col justify-between h-full',
				getCardBorderClass(content.status)
			)}
		>
			<div>
				<div className='flex justify-between items-start mb-2'>
					<h3 className='text-lg font-semibold text-brand-foreground mb-1 pr-2 break-words'>
						<Link
							to={viewLink}
							className='hover:text-primary-600 transition-colors'
						>
							{content.title}
						</Link>
					</h3>
					<span
						className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full whitespace-nowrap ${getStatusBadgeClass(content.status)}`}
					>
						{content.status.replace('_', ' ')}
					</span>
				</div>
				{/* Show snippet instead of idea */}
				<p className='text-sm text-gray-500 mb-3 line-clamp-2'>
					{getSnippet(content.content_body)}
				</p>
			</div>

			<div className='mt-auto pt-4 border-t border-gray-100'>
				<div className='flex justify-between items-center text-xs text-gray-500 mb-3'>
					<span>
						{/* Hide Due label if no date */}
						{content.due_date ? `Due: ${formatDate(content.due_date)}` : ''}
					</span>
					{/* Show rating if available */}
					{content.client_rating !== null &&
					content.client_rating !== undefined ? (
						<span className='flex items-center'>
							<Star className='w-3 h-3 text-yellow-400 mr-1' />
							{content.client_rating.toFixed(1)}
						</span>
					) : content.published_at ? ( // Show published date only if no rating
						<span>Published: {formatDate(content.published_at)}</span>
					) : null}
				</div>

				{/* Action Buttons */}
				<div className='flex space-x-2 justify-end'>
					{isClientView &&
						content.status === ContentStatus.PENDING_APPROVAL && (
							<Link
								to={viewLink}
								className='btn btn-secondary btn-sm px-3 py-1 text-xs'
							>
								{' '}
								{/* Smaller button */}
								<Clock className='h-3 w-3 mr-1' /> Review
							</Link>
						)}
					{isClientView &&
						content.status === ContentStatus.REVISION_REQUESTED && (
							<Link
								to={viewLink}
								className='btn btn-danger btn-sm px-3 py-1 text-xs'
							>
								{' '}
								{/* Danger style */}
								<AlertTriangle className='h-3 w-3 mr-1' /> Review Feedback
							</Link>
						)}
					{isClientView && content.status === ContentStatus.APPROVED && (
						<>
							<button
								onClick={handleCopy}
								className='btn btn-ghost btn-sm px-3 py-1 text-xs'
							>
								<Copy className='h-3 w-3 mr-1' /> Copy Text
							</button>
							<button
								onClick={handleMarkPostedClick}
								className='btn btn-success btn-sm px-3 py-1 text-xs'
							>
								{' '}
								{/* Success style */}
								<CheckCheck className='h-3 w-3 mr-1' /> Post now
							</button>
						</>
					)}
					{!isClientView && ( // Admin actions
						<Link
							to={editLink}
							className='btn btn-secondary btn-sm px-3 py-1 text-xs'
						>
							<Edit className='h-3 w-3 mr-1' /> Edit
						</Link>
					)}
					{/* General View button for non-actionable client items or admin */}
					{(!isClientView ||
						![
							ContentStatus.PENDING_APPROVAL,
							ContentStatus.REVISION_REQUESTED,
							ContentStatus.APPROVED,
						].includes(content.status)) && (
						<Link
							to={viewLink}
							className='btn btn-ghost btn-sm px-3 py-1 text-xs'
						>
							<Eye className='h-3 w-3 mr-1' /> View
						</Link>
					)}
				</div>
			</div>
		</div>
	);
};

export default ContentCard;
