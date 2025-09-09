# UI Deployment

This document describes how to build and deploy the React-based dashboard located in `ui/`.

## Install dependencies

```bash
cd ui
npm install
```

## Development server

Start a hot-reloading dev server with proxy rules for the API service and Prometheus:

```bash
npm run dev
```

The server proxies `/api` to `http://localhost:8000` and `/prometheus` to `http://localhost:9090`.

## Production build

Create an optimized production build:

```bash
npm run build
```

The compiled assets are written to `ui/dist` and can be served by any static file server.

To preview the build locally:

```bash
npm run preview
```

## Deployment

1. Build the project as shown above.
2. Copy the contents of `ui/dist` to your preferred static hosting environment.
3. Configure your reverse proxy to forward `/api` requests to the API service and `/prometheus` to the Prometheus server.
