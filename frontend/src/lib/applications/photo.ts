/** The API refuses anything bigger, so check before uploading and say so at once. */
export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
export const MAX_IMAGE_SIDE = 2000;
const JPEG_QUALITY = 0.85;

/**
 * Redraws a photo as a JPEG no bigger than 2000 px on its longest side. That makes uploads
 * faster on mobile data, and redrawing drops the EXIF data, including any GPS location.
 * PDFs, and images the browser can't decode, are returned unchanged; the API decides on those.
 */
export async function shrinkImage(file: File): Promise<File> {
	if (!file.type.startsWith('image/')) return file;
	try {
		// Applies the EXIF orientation, so a phone photo isn't saved sideways.
		const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
		const scale = Math.min(1, MAX_IMAGE_SIDE / Math.max(bitmap.width, bitmap.height));
		const width = Math.max(1, Math.round(bitmap.width * scale));
		const height = Math.max(1, Math.round(bitmap.height * scale));
		// A page canvas rather than OffscreenCanvas, which older Safari doesn't have.
		const canvas = document.createElement('canvas');
		canvas.width = width;
		canvas.height = height;
		const context = canvas.getContext('2d');
		if (!context) {
			bitmap.close();
			return file;
		}
		// JPEG has no transparency, so give see-through PNGs a white page instead of black.
		context.fillStyle = '#fff';
		context.fillRect(0, 0, width, height);
		context.drawImage(bitmap, 0, 0, width, height);
		bitmap.close();
		const blob = await new Promise<Blob | null>((done) => {
			canvas.toBlob(done, 'image/jpeg', JPEG_QUALITY);
		});
		if (!blob) return file;
		const name = file.name.replace(/\.[^.]*$/, '') + '.jpg';
		return new File([blob], name, { type: 'image/jpeg' });
	} catch {
		return file;
	}
}

export function formatBytes(bytes: number, locale: string): string {
	const format = (value: number, unit: 'kilobyte' | 'megabyte') =>
		new Intl.NumberFormat(locale, {
			style: 'unit',
			unit,
			maximumFractionDigits: 1
		}).format(value);
	return bytes < 1024 * 1024
		? format(bytes / 1024, 'kilobyte')
		: format(bytes / 1024 / 1024, 'megabyte');
}
