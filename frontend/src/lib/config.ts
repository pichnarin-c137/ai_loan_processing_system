/** Product name shown in the UI. Set VITE_APP_NAME in the repo-root .env to rename the app.
 * `||`, not `??`: an empty VITE_APP_NAME= line should fall back too. */
export const appName: string = import.meta.env.VITE_APP_NAME || 'Loan Desk';
