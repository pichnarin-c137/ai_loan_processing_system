import type { Locale } from '#lib/paraglide/runtime.js';

/** Every locale at once, so a missing translation fails the typecheck. */
export type Localized = Record<Locale, string>;

export interface Release {
	/** Day the change was shipped, as YYYY-MM-DD. */
	date: string;
	/** The pull requests that made the change. */
	prs: number[];
	title: Localized;
	items: Localized[];
}

export const repoUrl = 'https://github.com/pichnarin-c137/ai_loan_processing_system';

/**
 * The admin What's new page, newest first. Each PR adds its own entry at the top, in plain
 * language for people who use the app. Kept here rather than in messages/*.json: it's a growing
 * history, and one entry per PR is easier to keep than a pile of message keys.
 */
export const releases: Release[] = [
	{
		date: '2026-10-31',
		prs: [6],
		title: { en: 'What’s new page', km: 'ទំព័រអ្វីដែលថ្មី' },
		items: [
			{
				en: 'Admins have a What’s new page that lists every change to the app, newest first, in English and Khmer.',
				km: 'អ្នកគ្រប់គ្រងប្រព័ន្ធមានទំព័រ «អ្វីដែលថ្មី» ដែលបង្ហាញរាល់ការផ្លាស់ប្តូរនៃកម្មវិធី ថ្មីបំផុតនៅខាងលើ ជាភាសាអង់គ្លេស និងភាសាខ្មែរ។'
			},
			{
				en: 'Each change links to its full write-up.',
				km: 'ការផ្លាស់ប្តូរនីមួយៗមានតំណទៅកាន់ការពិពណ៌នាលម្អិត។'
			}
		]
	},
	{
		date: '2026-10-31',
		prs: [5],
		title: { en: 'Sign-in and invitations', km: 'ការចូលគណនី និងការអញ្ជើញ' },
		items: [
			{
				en: 'Sign in with your email and password. After several wrong tries, sign-in slows down so passwords can’t be guessed.',
				km: 'ចូលគណនីដោយប្រើអ៊ីមែល និងពាក្យសម្ងាត់។ បន្ទាប់ពីព្យាយាមខុសច្រើនដង ការចូលគណនីនឹងយឺតជាងមុន ដើម្បីកុំឱ្យគេទាយពាក្យសម្ងាត់បាន។'
			},
			{
				en: 'New accounts can only be made from an invite link that an admin creates, and the link sets the person’s role.',
				km: 'គណនីថ្មីអាចបង្កើតបានតែតាមតំណអញ្ជើញដែលអ្នកគ្រប់គ្រងប្រព័ន្ធបង្កើតប៉ុណ្ណោះ ហើយតំណនោះកំណត់តួនាទីរបស់អ្នកប្រើ។'
			},
			{
				en: 'Each invite link works once and expires. If creating the account fails, the link still works.',
				km: 'តំណអញ្ជើញនីមួយៗប្រើបានតែម្តង ហើយផុតកំណត់។ ប្រសិនបើការបង្កើតគណនីបរាជ័យ តំណនោះនៅតែប្រើបាន។'
			},
			{
				en: 'Admins have a Users page to create invite links, change roles, and block or unblock people.',
				km: 'អ្នកគ្រប់គ្រងប្រព័ន្ធមានទំព័រអ្នកប្រើប្រាស់ ដើម្បីបង្កើតតំណអញ្ជើញ ប្តូរតួនាទី និងបិទ ឬបើកគណនីអ្នកប្រើ។'
			},
			{
				en: 'Admins can’t change their own role, so they can’t lock themselves out by mistake.',
				km: 'អ្នកគ្រប់គ្រងប្រព័ន្ធមិនអាចប្តូរតួនាទីរបស់ខ្លួនឯងបានទេ ដូច្នេះមិនអាចបាត់សិទ្ធិដោយអចេតនា។'
			},
			{
				en: 'Customers, staff and admins each see only their own part of the app. People who aren’t signed in go to the sign-in page.',
				km: 'អតិថិជន បុគ្គលិក និងអ្នកគ្រប់គ្រងប្រព័ន្ធ ម្នាក់ៗឃើញតែផ្នែករបស់ខ្លួនក្នុងកម្មវិធី។ អ្នកដែលមិនទាន់ចូលគណនីនឹងត្រូវនាំទៅទំព័រចូលគណនី។'
			},
			{
				en: 'After signing in, you go back to the page you wanted. Links to other websites are ignored.',
				km: 'បន្ទាប់ពីចូលគណនី អ្នកនឹងត្រឡប់ទៅទំព័រដែលអ្នកចង់ចូល។ តំណទៅគេហទំព័រផ្សេងនឹងត្រូវរំលង។'
			},
			{
				en: 'Clear error messages in English and Khmer.',
				km: 'សារកំហុសច្បាស់លាស់ ជាភាសាអង់គ្លេស និងភាសាខ្មែរ។'
			}
		]
	},
	{
		date: '2026-10-31',
		prs: [4],
		title: {
			en: 'Storing applications and the history log',
			km: 'ការរក្សាទុកពាក្យស្នើសុំ និងកំណត់ត្រាប្រវត្តិ'
		},
		items: [
			{
				en: 'The app can now store loan applications, their documents, checks and decisions.',
				km: 'កម្មវិធីអាចរក្សាទុកពាក្យស្នើសុំកម្ចី ឯកសារ ការត្រួតពិនិត្យ និងការសម្រេចចិត្តបានហើយ។'
			},
			{
				en: 'Every action goes into a history log that can’t be changed or deleted.',
				km: 'រាល់សកម្មភាពត្រូវបានកត់ត្រាក្នុងកំណត់ត្រាប្រវត្តិ ដែលមិនអាចកែប្រែ ឬលុបបានទេ។'
			},
			{
				en: 'The six lending rules are saved as version 2026.1, so a later change becomes a new version instead of rewriting the old one.',
				km: 'គោលការណ៍ផ្តល់កម្ចីទាំងប្រាំមួយត្រូវបានរក្សាទុកជាកំណែ 2026.1 ដូច្នេះការផ្លាស់ប្តូរនៅពេលក្រោយនឹងក្លាយជាកំណែថ្មី ជំនួសឱ្យការកែកំណែចាស់។'
			}
		]
	},
	{
		// #2 went into the first PR's branch after it had merged, so #3 brought the same fix to main.
		date: '2026-10-31',
		prs: [2, 3],
		title: { en: 'A faster status page', km: 'ទំព័រស្ថានភាពលឿនជាងមុន' },
		items: [
			{
				en: 'When part of the system is down, the status page says so within seconds instead of hanging.',
				km: 'នៅពេលផ្នែកណាមួយនៃប្រព័ន្ធមិនដំណើរការ ទំព័រស្ថានភាពនឹងបង្ហាញក្នុងរយៈពេលប៉ុន្មានវិនាទី ជំនួសឱ្យការរង់ចាំយូរ។'
			},
			{
				en: 'The status page shows which part is down, not just that the server didn’t answer.',
				km: 'ទំព័រស្ថានភាពបង្ហាញថាផ្នែកណាមិនដំណើរការ មិនមែនត្រឹមតែប្រាប់ថាម៉ាស៊ីនមេមិនឆ្លើយតបនោះទេ។'
			},
			{
				en: 'Screen readers announce changes on the status page clearly.',
				km: 'កម្មវិធីអានអេក្រង់ប្រកាសការផ្លាស់ប្តូរនៅលើទំព័រស្ថានភាពយ៉ាងច្បាស់។'
			},
			{
				en: 'Behind the scenes, stricter automatic checks catch mistakes before changes go in.',
				km: 'នៅពីក្រោយ ការត្រួតពិនិត្យស្វ័យប្រវត្តិដែលតឹងរ៉ឹងជាងមុន ជួយចាប់កំហុសមុនពេលដាក់បញ្ចូលការផ្លាស់ប្តូរ។'
			}
		]
	},
	{
		date: '2026-10-31',
		prs: [1],
		title: { en: 'First version', km: 'កំណែដំបូង' },
		items: [
			{
				en: 'The first version of the app, with a customer area and a staff area, in English and Khmer.',
				km: 'កំណែដំបូងនៃកម្មវិធី មានផ្នែកសម្រាប់អតិថិជន និងផ្នែកសម្រាប់បុគ្គលិក ជាភាសាអង់គ្លេស និងភាសាខ្មែរ។'
			},
			{
				en: 'A status page shows whether each part of the system is working.',
				km: 'ទំព័រស្ថានភាពបង្ហាញថាផ្នែកនីមួយៗនៃប្រព័ន្ធកំពុងដំណើរការឬអត់។'
			},
			{
				en: 'Automatic checks run on every change to catch mistakes and block unsafe software packages.',
				km: 'ការត្រួតពិនិត្យស្វ័យប្រវត្តិដំណើរការលើរាល់ការផ្លាស់ប្តូរ ដើម្បីចាប់កំហុស និងរារាំងកញ្ចប់កម្មវិធីដែលមិនមានសុវត្ថិភាព។'
			}
		]
	}
];
