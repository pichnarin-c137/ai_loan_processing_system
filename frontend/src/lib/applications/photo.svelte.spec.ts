import { describe, expect, it } from 'vitest';
import { MAX_IMAGE_SIDE, shrinkImage } from './photo';

async function drawn(width: number, height: number, type: 'image/png' | 'image/jpeg') {
	const canvas = new OffscreenCanvas(width, height);
	const context = canvas.getContext('2d');
	if (!context) throw new Error('no 2d context');
	context.fillStyle = '#3366cc';
	context.fillRect(0, 0, width, height);
	return new Uint8Array(await (await canvas.convertToBlob({ type })).arrayBuffer());
}

/** Inserts a small EXIF block (with a GPS-like marker string) right after the JPEG start marker. */
function withExif(jpeg: Uint8Array): Uint8Array<ArrayBuffer> {
	const tiff = [0x4d, 0x4d, 0x00, 0x2a, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00];
	const marker = [...new TextEncoder().encode('GPS-SECRET-MARKER')];
	const body = [...new TextEncoder().encode('Exif\0\0'), ...tiff, ...marker];
	const length = body.length + 2;
	const segment = [0xff, 0xe1, length >> 8, length & 0xff, ...body];
	return new Uint8Array([...jpeg.slice(0, 2), ...segment, ...jpeg.slice(2)]);
}

function contains(bytes: Uint8Array, text: string): boolean {
	return new TextDecoder('latin1').decode(bytes).includes(text);
}

async function size(file: Blob) {
	const bitmap = await createImageBitmap(file);
	const result = { width: bitmap.width, height: bitmap.height };
	bitmap.close();
	return result;
}

describe('shrinkImage', () => {
	it('scales a large photo down to 2000 px on its longest side, as JPEG', async () => {
		const png = new File([await drawn(3000, 1500, 'image/png')], 'scan.png', { type: 'image/png' });
		const out = await shrinkImage(png);
		expect(out.type).toBe('image/jpeg');
		expect(out.name).toBe('scan.jpg');
		expect(await size(out)).toEqual({ width: MAX_IMAGE_SIDE, height: 1000 });
	});

	it('keeps the size of a small photo', async () => {
		const png = new File([await drawn(800, 600, 'image/png')], 'id.png', { type: 'image/png' });
		expect(await size(await shrinkImage(png))).toEqual({ width: 800, height: 600 });
	});

	it('drops EXIF data, such as the location', async () => {
		const original = withExif(await drawn(400, 300, 'image/jpeg'));
		expect(contains(original, 'Exif')).toBe(true);
		const out = await shrinkImage(new File([original], 'photo.jpeg', { type: 'image/jpeg' }));
		const bytes = new Uint8Array(await out.arrayBuffer());
		expect(contains(bytes, 'Exif')).toBe(false);
		expect(contains(bytes, 'GPS-SECRET-MARKER')).toBe(false);
	});

	it('leaves PDFs, and images it cannot read, unchanged', async () => {
		const pdf = new File(['%PDF-1.7'], 'statement.pdf', { type: 'application/pdf' });
		expect(await shrinkImage(pdf)).toBe(pdf);
		const broken = new File(['not an image'], 'photo.jpg', { type: 'image/jpeg' });
		expect(await shrinkImage(broken)).toBe(broken);
	});
});
