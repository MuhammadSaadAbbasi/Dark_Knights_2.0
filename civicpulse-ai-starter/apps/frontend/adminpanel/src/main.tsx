import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './view/App';
import './view/style.css';

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
