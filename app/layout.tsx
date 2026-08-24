import type {Metadata} from 'next';
import './globals.css';
export const metadata:Metadata={title:'Gobierno en claro · Mapa del Ejecutivo colombiano',description:'Explora la estructura, competencias, responsables y cambios del Gobierno colombiano.',openGraph:{title:'Gobierno en claro',description:'¿Quién hace qué en el Gobierno? Estructura, competencias y cambios del Ejecutivo colombiano.',images:[{url:'/og.png',width:1200,height:630,alt:'Gobierno en claro'}]},twitter:{card:'summary_large_image',title:'Gobierno en claro',description:'¿Quién hace qué en el Gobierno?',images:['/og.png']}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="es"><body>{children}</body></html>}
