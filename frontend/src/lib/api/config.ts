/**
 * API Configuration
 * Centralized configuration for API base URL
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Get the full URL for a static asset (like uploaded images)
 */
export function getImageUrl(imagePath: string | null | undefined): string {
	if (!imagePath) return '';
	// If imagePath already includes the full URL, return it as is
	if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
		return imagePath;
	}
	// Otherwise, prepend the API base URL
	return `${API_BASE_URL}${imagePath}`;
}









