import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import GobiernoApp from '../app/page';
import '../app/globals.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <GobiernoApp />
  </StrictMode>,
);
