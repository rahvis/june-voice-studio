# Voice Cloning Frontend

A modern, responsive web application for Azure Voice Cloning System built with Next.js, TypeScript, and Tailwind CSS.

## Features

- **Authentication & Authorization**: Azure Entra ID integration with role-based access control
- **Voice Enrollment**: Multi-step voice recording and upload interface with consent management
- **Real-time Synthesis**: Text-to-speech synthesis with custom voice models
- **Dashboard**: Comprehensive overview of voice models, synthesis history, and system status
- **Responsive Design**: Mobile-first design with dark/light theme support
- **Modern UI**: Built with Framer Motion animations and Lucide React icons

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand + React Query
- **Authentication**: Azure MSAL (Microsoft Authentication Library)
- **UI Components**: Custom component library with Radix UI primitives
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Forms**: React Hook Form

## Prerequisites

- Node.js 18+ 
- npm 9+ or yarn
- Azure subscription with:
  - Azure Entra ID (formerly Azure AD)
  - App registration for authentication
  - Azure AI Speech Service
  - Azure AI Translator Service
  - Azure OpenAI Service

## Environment Configuration

Create a `.env.local` file in the frontend directory with the following variables:

```bash
# Azure Configuration
NEXT_PUBLIC_AZURE_CLIENT_ID=your_azure_client_id_here
NEXT_PUBLIC_AZURE_TENANT_ID=your_azure_tenant_id_here
NEXT_PUBLIC_REDIRECT_URI=http://localhost:3000
NEXT_PUBLIC_POST_LOGOUT_REDIRECT_URI=http://localhost:3000

# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

# Feature Flags
NEXT_PUBLIC_ENABLE_VOICE_ENROLLMENT=true
NEXT_PUBLIC_ENABLE_REAL_TIME_SYNTHESIS=true
NEXT_PUBLIC_ENABLE_MULTI_LANGUAGE=true

# Development Settings
NEXT_PUBLIC_DEBUG_MODE=true
NEXT_PUBLIC_LOG_LEVEL=debug
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd azure/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your Azure configuration
   ```

4. **Run the development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

5. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── dashboard/         # Dashboard page
│   │   ├── synthesis/         # Voice synthesis page
│   │   ├── voice-enrollment/  # Voice enrollment page
│   │   ├── globals.css        # Global styles
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Home page
│   ├── components/            # Reusable UI components
│   │   └── ui/               # Base UI components
│   │       ├── Button.tsx    # Button component
│   │       ├── Card.tsx      # Card component
│   │       ├── Input.tsx     # Input component
│   │       ├── Loading.tsx   # Loading component
│   │       └── index.ts      # Component exports
│   ├── contexts/             # React contexts
│   │   ├── AuthContext.tsx   # Authentication context
│   │   ├── QueryContext.tsx  # React Query context
│   │   └── ThemeContext.tsx  # Theme management context
│   ├── hooks/                # Custom React hooks
│   ├── lib/                  # Utility libraries
│   ├── types/                # TypeScript type definitions
│   └── utils/                # Helper functions
├── public/                   # Static assets
├── package.json              # Dependencies and scripts
├── next.config.js            # Next.js configuration
├── tailwind.config.js        # Tailwind CSS configuration
└── tsconfig.json             # TypeScript configuration
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler check
- `npm run test` - Run Jest tests
- `npm run test:watch` - Run tests in watch mode
- `npm run test:coverage` - Run tests with coverage report

## Key Components

### Authentication Context (`AuthContext.tsx`)
- Azure Entra ID integration using MSAL
- Role-based access control
- User profile management
- Token management and refresh

### Voice Enrollment (`voice-enrollment/page.tsx`)
- Multi-step enrollment process
- Audio recording and upload
- Consent management
- Progress tracking

### Voice Synthesis (`synthesis/page.tsx`)
- Text input and processing
- Voice selection
- Real-time synthesis
- Audio playback controls

### Dashboard (`dashboard/page.tsx`)
- Voice model management
- Synthesis statistics
- System status monitoring
- Quick actions

## UI Components

### Button
- Multiple variants: primary, secondary, outline, ghost, danger
- Different sizes: sm, md, lg, xl
- Loading states and icons
- Full-width option

### Card
- Flexible layout with header, content, and footer
- Multiple variants: default, elevated, outlined, filled
- Hover effects and animations

### Input
- Form input with labels and helper text
- Error states and validation
- Icon support (left/right)
- Different sizes and variants

### Loading
- Multiple loading animations: spinner, dots, bars, pulse
- Customizable sizes and text
- Full-screen overlay option

## Styling

The application uses Tailwind CSS with a custom design system:

- **Colors**: Extended color palette with semantic naming
- **Typography**: Custom font scales and weights
- **Spacing**: Consistent spacing scale
- **Animations**: Smooth transitions and micro-interactions
- **Dark Mode**: Automatic theme switching with system preference detection

## Responsive Design

- Mobile-first approach
- Breakpoint system: sm, md, lg, xl
- Flexible grid layouts
- Touch-friendly interactions
- Optimized for all device sizes

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development Guidelines

### Code Style
- Use TypeScript for all new code
- Follow ESLint configuration
- Use Prettier for code formatting
- Write meaningful component and function names

### Component Structure
- Use functional components with hooks
- Implement proper TypeScript interfaces
- Add proper error boundaries
- Include loading states

### State Management
- Use React Query for server state
- Use local state for UI state
- Implement proper error handling
- Use optimistic updates where appropriate

### Performance
- Implement proper memoization
- Use dynamic imports for code splitting
- Optimize bundle size
- Implement proper loading states

## Testing

The application includes Jest testing setup:

- Unit tests for components
- Integration tests for pages
- Mock data for testing
- Coverage reporting

## Deployment

### Build for Production
```bash
npm run build
```

### Environment Variables for Production
- Set all `NEXT_PUBLIC_*` variables
- Configure Azure services
- Set up proper redirect URIs
- Configure API endpoints

### Deployment Options
- Azure Static Web Apps
- Vercel
- Netlify
- Docker containers

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify Azure app registration configuration
   - Check redirect URI settings
   - Ensure proper scopes are configured

2. **Build Errors**
   - Clear `.next` directory
   - Check TypeScript errors
   - Verify all dependencies are installed

3. **Styling Issues**
   - Clear browser cache
   - Check Tailwind CSS configuration
   - Verify CSS imports

### Debug Mode
Enable debug mode by setting `NEXT_PUBLIC_DEBUG_MODE=true` in your environment variables.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Check the documentation
- Review existing issues
- Create a new issue with detailed information
- Contact the development team

## Roadmap

- [ ] Multi-language support
- [ ] Advanced voice customization
- [ ] Batch synthesis capabilities
- [ ] API rate limiting and quotas
- [ ] Advanced analytics and reporting
- [ ] Mobile app development
- [ ] Integration with external platforms
