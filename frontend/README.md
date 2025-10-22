# Graph RAG Frontend

Beautiful, responsive React + TypeScript frontend for Graph RAG with Cytoscape.js visualization.

## Features

- ✨ **Dual Answer Display** - Side-by-side comparison of general vs graph RAG answers
- 🎨 **Beautiful UI** - Tailwind CSS with soft shadows, rounded corners, smooth transitions
- 📊 **Interactive Graph** - Cytoscape.js visualization with community colors
- 🏷️ **Smart Citations** - Inline ticket ID highlighting in answers
- 🎯 **Cluster Filtering** - Click clusters to focus on specific communities
- 📱 **Responsive Design** - Works on desktop and tablet
- ⚡ **Fast** - Optimized with Vite and parallel API calls

## Setup

### Install Dependencies

```bash
npm install
```

### Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:
```
VITE_API_URL=http://127.0.0.1:8000
```

### Run Development Server

```bash
npm run dev
```

Open http://localhost:5173

## Build for Production

```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Project Structure

```
src/
├── components/
│   ├── QueryBox.tsx       # Search input with examples
│   ├── AnswerCard.tsx     # Dual answer display
│   ├── GraphPanel.tsx     # Cytoscape graph visualization
│   └── ClusterLegend.tsx  # Community legend with colors
├── lib/
│   ├── api.ts            # API client functions
│   └── utils.ts          # Utility functions
├── App.tsx               # Main application
├── main.tsx             # Entry point
└── index.css            # Tailwind + custom styles
```

## Components

### QueryBox
- Large search input with examples
- Submit button with loading state
- Enter key to submit
- Example queries for quick start

### AnswerCard
- Two panels: General (purple) vs Graph RAG (blue gradient)
- Community badges showing clusters
- Inline ticket citations (highlighted)
- Provenance info (tickets, sections, communities)
- Token usage display

### GraphPanel
- Cytoscape.js graph visualization
- Nodes colored by community
- Node size based on degree/importance
- Tooltip with cluster reason on hover
- Controls: zoom, fit, layout change
- Click to highlight connected nodes

### ClusterLegend
- List of communities with colors
- Click to filter/highlight cluster
- Shows size and reason for each cluster
- Smooth transitions

## Styling

### Color Palette
- **General Answer**: Purple theme (#8b5cf6)
- **Graph RAG**: Blue gradient (#3b82f6 → #4f46e5)
- **Communities**: 10-color palette rotating by cluster ID
- **Background**: Gradient from gray-50 via blue-50 to indigo-50

### Design Features
- Soft shadows with hover effects
- Rounded corners (rounded-xl, rounded-lg)
- Smooth transitions (duration-150, duration-200)
- Tasteful spacing with max-width constraints
- Glass morphism effect on header
- Gradient accents on key elements

## API Integration

### API Client (`src/lib/api.ts`)
- `ask(query)` - POST /ask for dual answers
- `fetchGraph(query)` - GET /graph/subgraph for visualization
- `checkHealth()` - GET /health for status
- Type-safe with TypeScript interfaces

### Parallel Requests
Both `ask()` and `fetchGraph()` are called in parallel for faster response.

## Graph Visualization

### Node Types
- **Ticket nodes**: Large, colored by community, size by degree
- **Section nodes**: Small, gray, shows section key

### Edge Types
- **SIMILAR_TO**: Solid, width by similarity score
- **HAS_SECTION**: Dashed, thin, low opacity

### Layouts
- **cose-bilkent**: Force-directed (default)
- **circle**: Circular layout
- **grid**: Grid layout

Click layout button to cycle through options.

### Interactions
- **Hover**: Show tooltip with cluster info
- **Click node**: Highlight neighbors
- **Click cluster**: Filter/highlight community
- **Zoom/Pan**: Mouse wheel + drag

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://127.0.0.1:8000` | Backend API base URL |

## Dependencies

### Core
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool

### Styling
- **Tailwind CSS** - Utility-first CSS
- **lucide-react** - Beautiful icons
- **clsx + tailwind-merge** - Conditional classes

### Data & API
- **axios** - HTTP client
- **cytoscape** - Graph visualization
- **cytoscape-cose-bilkent** - Layout algorithm

### UI Components
- **@radix-ui** - Accessible primitives
- **framer-motion** - Smooth animations

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Performance

- **Bundle size**: ~500KB (gzipped)
- **First load**: <2s on 3G
- **Parallel API calls**: Dual answers + graph fetched simultaneously
- **Optimized images**: None (icon library only)
- **Code splitting**: Automatic via Vite

## Troubleshooting

### API Connection Issues
1. Check backend is running: `curl http://127.0.0.1:8000/health`
2. Verify VITE_API_URL in `.env`
3. Check browser console for CORS errors

### Graph Not Rendering
1. Ensure Cytoscape is loaded: check browser console
2. Verify data format matches SubgraphResponse type
3. Check container has height (inspect element)

### Styling Issues
1. Rebuild Tailwind: `npm run build`
2. Clear cache: `rm -rf node_modules/.vite`
3. Restart dev server

## Development Tips

### Hot Module Replacement
Vite HMR preserves state during development. Changes to components update instantly without full reload.

### TypeScript
Enable strict mode for better type safety. All API responses are fully typed.

### Debugging
- Use React DevTools for component inspection
- Cytoscape debug: `window.cy = cyRef.current` in console
- API calls visible in Network tab

## Customization

### Change Colors
Edit `COMMUNITY_COLORS` in `GraphPanel.tsx` or Tailwind theme in `tailwind.config.js`.

### Add More Examples
Update `exampleQueries` in `QueryBox.tsx`.

### Modify Graph Style
Edit Cytoscape styles in `GraphPanel.tsx` (node colors, sizes, edge styles).

## License

MIT
