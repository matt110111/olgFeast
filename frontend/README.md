# olgFeast Frontend

A modern React TypeScript frontend for the olgFeast restaurant management system.

## Features

- **Modern UI/UX**: Built with React, TypeScript, and Tailwind CSS
- **Authentication**: JWT-based login/register with protected routes
- **Menu Management**: Browse and manage food items
- **Shopping Cart**: Add items and manage quantities
- **Order Tracking**: View order history and status
- **Real-time Updates**: WebSocket integration for live notifications
- **Responsive Design**: Mobile-first responsive layout

## Tech Stack

- **React 18** with TypeScript
- **React Router** for navigation
- **Tailwind CSS** for styling
- **Axios** for API communication
- **Lucide React** for icons
- **WebSocket** for real-time updates

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- FastAPI backend running on http://localhost:8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

## Project Structure

```
src/
├── components/          # Reusable React components
│   ├── Auth/           # Authentication components
│   ├── Layout/         # Layout components (Header, Layout)
│   └── Menu/           # Menu-related components
├── contexts/           # React contexts
│   └── AuthContext.tsx # Authentication context
├── services/           # API and WebSocket services
│   ├── api.ts         # FastAPI client
│   └── websocket.ts   # WebSocket service
├── types/              # TypeScript type definitions
│   └── index.ts       # All type definitions
├── App.tsx            # Main App component
└── index.css          # Global styles with Tailwind
```

## Available Scripts

- `npm start` - Runs the app in development mode
- `npm run build` - Builds the app for production
- `npm test` - Launches the test runner
- `npm run eject` - Ejects from Create React App

## API Integration

The frontend integrates with the FastAPI backend through:

- **Authentication**: `/api/v1/auth/*`
- **Menu**: `/api/v1/menu/*`
- **Cart**: `/api/v1/cart/*`
- **Orders**: `/api/v1/orders/*`
- **Operations**: `/api/v1/operations/*`

## WebSocket Integration

Real-time features are powered by WebSocket connections:

- **Kitchen Display**: `ws://localhost:8000/ws/kitchen/display`
- **Order Updates**: `ws://localhost:8000/ws/orders/updates`
- **Admin Dashboard**: `ws://localhost:8000/ws/admin/dashboard`

## Demo Credentials

- **Staff User**: admin / admin123
- **Customer User**: customer / customer123

## Development

### Adding New Components

1. Create component in appropriate directory under `src/components/`
2. Export from component file
3. Import and use in parent components

### API Integration

1. Add new API endpoints in `src/services/api.ts`
2. Update types in `src/types/index.ts` if needed
3. Use in components with proper error handling

### Styling

- Use Tailwind CSS classes for styling
- Follow the design system defined in `tailwind.config.js`
- Use Lucide React icons for consistency

## Build and Deployment

### Production Build

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

### Environment Variables

Create a `.env` file for environment-specific configuration:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## Contributing

1. Follow TypeScript best practices
2. Use functional components with hooks
3. Implement proper error handling
4. Add loading states for async operations
5. Write meaningful component and function names

## License

This project is part of the olgFeast restaurant management system.