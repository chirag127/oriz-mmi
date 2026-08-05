// @ts-check
import { defineConfig } from 'astro/config';

// Static dark dial site for mmi.oriz.in. Reads ../data/latest.json + history at
// build time (the scraper commits it hourly; CF Pages rebuilds on push).
export default defineConfig({
  site: 'https://mmi.oriz.in',
  output: 'static',
  trailingSlash: 'ignore',
});
