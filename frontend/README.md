# Kidney Ultrasound AI Detection - Frontend

A modern React frontend for the kidney ultrasound classification system.

## Features

- 🖼️ Drag & drop image upload with preview
- 🔄 Real-time backend health monitoring
- 📊 Detailed prediction results with confidence scores
- 🎨 Clean, responsive UI with Tailwind CSS
- ⚡ Fast development with Vite
- 📝 Full TypeScript support

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **React Dropzone** - File upload

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx           # Entry point
│   ├── App.tsx            # Root component
│   ├── index.css          # Global styles
│   ├── api/
│   │   └── api.ts         # API client
│   ├── components/
│   │   ├── ImageUpload.tsx
│   │   ├── PredictionResult.tsx
│   │   └── Loader.tsx
│   ├── pages/
│   │   └── Home.tsx       # Main page
│   └── types/
│       └── types.ts       # TypeScript types
├── index.html
├── package.json
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
└── vite.config.ts
```

## Installation

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Open in browser**
   ```
   Use the URL shown in terminal (for example: http://localhost:5173)
   ```

## Configuration

### Backend URL

By default, the frontend connects to `http://localhost:8000`. To change this:

1. Create a `.env` file in the frontend directory:
   ```env
   VITE_API_URL=http://your-backend-url:8000
   ```

2. Or modify `src/api/api.ts` directly.

### Proxy (Development)

The Vite dev server proxies API requests to avoid CORS issues. Port is not hardcoded; by default Vite chooses its default/next free port.  
If needed, set a custom port in `.env`:

```env
VITE_DEV_PORT=5000
```

See `vite.config.ts`:

```typescript
server: {
  port: Number(env.VITE_DEV_PORT) || undefined,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
},
```

## Usage

### Basic Flow

1. **Start the backend server** (see backend README)
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start the frontend**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Upload an image** via drag & drop or file picker

4. **Click "Analyze Image"** to get predictions

5. **View results** with confidence scores and severity levels

### API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/upload` | POST | Upload image |
| `/api/v1/predict` | POST | Run prediction |
| `/api/v1/predict/model/info` | GET | Get model info |
| `/api/v1/predict/model/load` | POST | Load model |

## Building for Production

```bash
# Build
npm run build

# Preview build
npm run preview
```

Output will be in the `dist/` directory.

## Deployment

### Static Hosting (Vercel, Netlify, etc.)

1. Build the project
2. Deploy the `dist/` folder
3. Configure environment variable for API URL

### Docker

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Development

### Available Scripts

- `npm run dev` - Start dev server
- `npm run build` - Production build
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Adding New Components

1. Create component in `src/components/`
2. Export from component file
3. Import in pages/other components

### Type Definitions

All API types are defined in `src/types/types.ts`. Update when backend API changes.

## Troubleshooting

### CORS Errors

- Ensure backend CORS is configured
- Use the Vite proxy in development
- Set correct `VITE_API_URL` in production

### Backend Connection Failed

- Check backend is running on port 8000
- Verify `VITE_API_URL` is correct
- Check network/firewall settings

### Build Errors

- Clear `node_modules` and reinstall
- Check TypeScript errors
- Ensure all imports are correct

## License

MIT License
