import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import contentService, {
	Content,
	ContentStatus,
} from '../../services/contents';
import ContentView from '../../components/contents/ContentView';
import { useAuth } from '../../context/AuthContext';
import RatingModal from '../../components/common/RatingModal';
import CustomStarRating from '../../components/common/CustomStarRating'; // Import CustomStarRating
import { ArrowLeft, FileText } from 'lucide-react'; // Added FileText icon
import StrategyViewModal from '../../components/strategies/StrategyViewModal'; // Import Strategy Modal
import strategyService, { Strategy } from '../../services/strategies'; // Import Strategy service and type

const ClientContentViewPage: React.FC = () => {
	const { id } = useParams<{ id: string }>();
	const navigate = useNavigate();
	const { user } = useAuth();
	const contentId = parseInt(id || '0', 10);

	const [content, setContent] = useState<Content | null>(null);
	const [strategy, setStrategy] = useState<Strategy | null>(null); // State for strategy
	const [loading, setLoading] = useState<boolean>(true);
	const [error, setError] = useState<string | null>(null);
	const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
	const [showRevisionModal, setShowRevisionModal] = useState<boolean>(false);
	const [revisionComment, setRevisionComment] = useState<string>('');
	const [pendingContentIds, setPendingContentIds] = useState<number[]>([]);
	const [currentIndex, setCurrentIndex] = useState<number>(-1);
	const [showRatingModal, setShowRatingModal] = useState<boolean>(false);
	const [showStrategyModal, setShowStrategyModal] = useState<boolean>(false); // State for strategy modal

	// Define fetchContent outside useEffect, memoize with useCallback
	const fetchContent = useCallback(async () => {
		if (!contentId) {
			setError('Invalid Content ID');
			return;
		}
		try {
			const data = await contentService.getById(contentId);
			if (user?.role !== 'client' || data.client_id !== user?.client_id) {
				setError('You do not have permission to view this content.');
				setContent(null);
			} else {
				setContent(data);
				setError(null);
				// Fetch associated strategy after fetching content
				try {
					const strategyData = await strategyService.getByClientId(
						data.client_id
					);
					setStrategy(strategyData);
				} catch (strategyErr: any) {
					if (strategyErr.response && strategyErr.response.status === 404) {
						setStrategy(null); // No strategy found is okay
					} else {
						console.error('Failed to fetch strategy for content:', strategyErr);
						// Non-critical error, don't block content view
					}
				}
			}
		} catch (err) {
			console.error('Failed to fetch content:', err);
			setError('Failed to load content piece.');
			setContent(null); // Clear content on error
			setStrategy(null); // Clear strategy on error
		}
	}, [contentId, user]); // Dependencies for fetchContent

	// Load content and pending IDs on mount/change
	useEffect(() => {
		setLoading(true);
		fetchContent().finally(() => setLoading(false));

		const fetchPendingIds = async () => {
			if (!user?.client_id) return;
			try {
				const pending = await contentService.getAll(
					user.client_id,
					ContentStatus.PENDING_APPROVAL
				);
				const ids = pending.map((c) => c.id).sort((a, b) => a - b);
				setPendingContentIds(ids);
				const currentIdx = ids.indexOf(contentId);
				setCurrentIndex(currentIdx);
			} catch (err) {
				console.error('Failed to fetch pending content IDs:', err);
			}
		};
		fetchPendingIds();
	}, [fetchContent, contentId, user]);

	// Opens the rating modal instead of directly approving
	const handleApproveClick = () => {
		if (!content || content.status !== ContentStatus.PENDING_APPROVAL) return;
		setShowRatingModal(true);
	};

	// Called when the rating modal is closed (either submitted or cancelled)
	const handleRatingModalClose = async (rated: boolean) => {
		setShowRatingModal(false);
		if (!rated) {
			await submitApprovalOnly();
		}
	};

	// Function called by the modal on successful rating submission
	const submitRating = async (rating: number) => {
		if (!content) throw new Error('Content not loaded');
		await contentService.rate(content.id, rating);
	};

	// Function to approve content AND submit rating (called from modal)
	const submitApprovalAndRating = async (rating: number) => {
		if (!content) return;
		setIsSubmitting(true);
		setError(null);
		try {
			await contentService.approve(content.id);
			await submitRating(rating);
			navigate('/client/library');
		} catch (err: any) {
			console.error('Failed to approve and rate content:', err);
			setError(
				err.message || 'Failed to approve or rate content. Please try again.'
			);
			throw err;
		} finally {
			setIsSubmitting(false);
		}
	};

	// Function to approve content ONLY (called when modal closed without rating)
	const submitApprovalOnly = async () => {
		if (!content) return;
		setIsSubmitting(true);
		setError(null);
		try {
			await contentService.approve(content.id);
			navigate('/client/library');
		} catch (err: any) {
			console.error('Failed to approve content:', err);
			setError(err.message || 'Failed to approve content. Please try again.');
		} finally {
			setIsSubmitting(false);
		}
	};

	const handleOpenRevisionModal = () => {
		setRevisionComment('');
		setShowRevisionModal(true);
	};

	const handleRequestRevision = async () => {
		if (!content || !revisionComment.trim()) return;
		setIsSubmitting(true);
		setError(null);
		try {
			await contentService.requestRevision(content.id, revisionComment.trim());
			setShowRevisionModal(false);
			navigate('/client/dashboard');
		} catch (err) {
			console.error('Failed to request revision:', err);
			setError('Failed to request revision. Please try again.');
			// Keep modal open on error? Or close? Closing for now.
			setShowRevisionModal(false);
		} finally {
			setIsSubmitting(false);
		}
	};

	const handleMarkAsPosted = async () => {
		if (!content) return;
		setIsSubmitting(true);
		setError(null);
		try {
			await contentService.postNow(content.id);
			navigate('/client/library');
			// navigate(`/dashboard/linkedin/schedule?id=${content.id}`);
		} catch (err: any) {
			console.error('Failed to post content:', err);
			setError(err.message || 'Failed to post content. Please try again.');
		} finally {
			setIsSubmitting(false);
		}
	};

	if (loading) {
		return (
			<div className='flex justify-center items-center p-8'>
				<div className='animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600'></div>
			</div>
		);
	}

	if (error || !content) {
		return (
			<div className='container mx-auto px-4 py-8'>
				<div
					className='m-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded'
					role='alert'
				>
					<strong className='font-bold'>Error!</strong>
					<span className='block sm:inline'>
						{' '}
						{error || 'Content not found or not accessible.'}
					</span>
				</div>
				<button
					onClick={() => navigate('/client/dashboard')}
					className='btn btn-secondary mt-4'
				>
					Back to Dashboard
				</button>
			</div>
		);
	}

	const canTakeAction = content.status === ContentStatus.PENDING_APPROVAL;
	const canMarkAsPosted =
		content.status === ContentStatus.APPROVED && !content.published_at;
	const canEdit = content.status !== ContentStatus.PUBLISHED;

	return (
		<div className='container mx-auto'>
			<div className='mb-6 flex justify-between items-center flex-wrap gap-2'>
				{/* Add button to view strategy */}
				{strategy && (
					<button
						onClick={() => setShowStrategyModal(true)}
						className='btn btn-outline btn-sm text-xs'
					>
						<FileText className='mr-1.5 h-3 w-3' /> View Strategy
					</button>
				)}
				{!strategy && <div></div>} {/* Spacer if no strategy */}
				<div className="flex gap-2">
					{canEdit && (
						<button
							onClick={() => navigate(`/client/contents/${content.id}/edit`)}
							className='btn btn-primary'
						>
							Edit Content
						</button>
					)}
					<button
						onClick={() => navigate('/client/library')}
						className='btn btn-secondary'
					>
						<ArrowLeft className='mr-2 h-4 w-4' /> Back to Library
					</button>
				</div>
			</div>

			{/* Navigation and Action Buttons (Sticky Header) */}
			{canTakeAction && (
				<div className='sticky top-[calc(4rem+1px)] z-10 bg-white shadow-md mb-6 rounded-b-lg border-t border-gray-200'>
					<div className='max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-3'>
						<h2 className='text-lg font-medium text-gray-900 mb-2 md:mb-0 md:inline-block md:mr-4'>
							Actions
						</h2>
						{error && (
							<div
								className='mb-2 text-sm bg-red-100 border border-red-400 text-red-700 px-3 py-1 rounded'
								role='alert'
							>
								{error}
							</div>
						)}
						<div className='flex flex-wrap gap-2'>
							<button
								onClick={handleApproveClick}
								disabled={isSubmitting}
								className='btn btn-success'
								style={{ background: 'lightgreen' }}
							>
								{isSubmitting ? 'Processing...' : 'Approve Content'}
							</button>
							<button
								onClick={handleOpenRevisionModal}
								disabled={isSubmitting}
								className='btn btn-secondary'
							>
								Request Revision
							</button>
							{/* Sequential Navigation Buttons */}
							<button
								onClick={() =>
									navigate(
										`/client/contents/${pendingContentIds[currentIndex - 1]}`
									)
								}
								disabled={currentIndex <= 0}
								className='ml-auto btn btn-ghost btn-sm px-3 py-1.5 text-xs'
							>
								&larr; Previous
							</button>
							<button
								onClick={() =>
									navigate(
										`/client/contents/${pendingContentIds[currentIndex + 1]}`
									)
								}
								disabled={
									currentIndex < 0 ||
									currentIndex >= pendingContentIds.length - 1
								}
								className='btn btn-ghost btn-sm px-3 py-1.5 text-xs'
							>
								Next &rarr;
							</button>
						</div>
					</div>
				</div>
			)}

			{/* Display Content */}
			<div className='card p-0 overflow-hidden'>
				<ContentView content={content} onContentUpdated={fetchContent} />
			</div>

			{/* Display Rating if available */}
			{content.client_rating !== null &&
				content.client_rating !== undefined && (
					<div className='mt-6 flex items-center gap-2'>
						<span className='text-sm font-medium text-gray-600'>
							Your Rating:
						</span>
						<CustomStarRating
							rating={content.client_rating}
							readOnly={true}
							size={20}
						/>
					</div>
				)}

			{/* "Mark as Posted" Button */}
			{canMarkAsPosted && (
				<div className='mt-6 flex justify-end gap-2'>
					<button
						onClick={handleMarkAsPosted}
						disabled={isSubmitting}
						className='btn btn-secondary'
					>
						{isSubmitting ? 'Posting...' : 'Post now'}
					</button>
					<button
						onClick={() => navigate(`/client/contents/${content.id}/edit?schedule=true`)}
						className='btn btn-primary'
					>
						Schedule post
					</button>
				</div>
			)}

			{/* Revision Request Modal */}
			{showRevisionModal && (
				<div className='fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4'>
					<div className='relative mx-auto border border-gray-200 w-full max-w-md shadow-xl rounded-lg bg-white'>
						<div className='flex justify-between items-center border-b p-5'>
							<h3 className='text-lg font-semibold text-brand-foreground'>
								Request Revision
							</h3>
							<button
								onClick={() => setShowRevisionModal(false)}
								className='text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm p-1.5 ml-auto inline-flex items-center'
								aria-label='Close modal'
							>
								<svg
									className='w-5 h-5'
									fill='currentColor'
									viewBox='0 0 20 20'
									xmlns='http://www.w3.org/2000/svg'
								>
									<path
										fillRule='evenodd'
										d='M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z'
										clipRule='evenodd'
									></path>
								</svg>
							</button>
						</div>
						<div className='p-6'>
							<label htmlFor='revisionComment' className='form-label mb-1'>
								Please provide feedback for revision:{' '}
								<span className='text-red-600'>*</span>
							</label>
							<textarea
								id='revisionComment'
								rows={4}
								className='form-input w-full'
								value={revisionComment}
								onChange={(e) => setRevisionComment(e.target.value)}
								placeholder='e.g., Please expand on section 2...'
							/>
						</div>
						<div className='flex justify-end items-center border-t p-4 space-x-2'>
							<button
								onClick={() => setShowRevisionModal(false)}
								className='btn btn-secondary'
								disabled={isSubmitting}
							>
								Cancel
							</button>
							<button
								onClick={handleRequestRevision}
								disabled={isSubmitting || !revisionComment.trim()}
								className='btn btn-danger' // Use danger style
							>
								{isSubmitting ? 'Submitting...' : 'Submit Revision Request'}
							</button>
						</div>
					</div>
				</div>
			)}

			{/* Rating Modal */}
			<RatingModal
				isOpen={showRatingModal}
				onClose={handleRatingModalClose}
				onSubmitRating={submitApprovalAndRating}
				contentTitle={content.title}
			/>

			{/* Strategy Modal */}
			<StrategyViewModal
				strategy={strategy}
				isOpen={showStrategyModal}
				onClose={() => setShowStrategyModal(false)}
			/>
		</div>
	);
};

export default ClientContentViewPage;
